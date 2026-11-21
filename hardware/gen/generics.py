"""Generic schematic symbols (R, C, L, D, LED, FET, test point, jumper, crystal, switch...).

Built in code so the project doesn't depend on KiCad's standard symbol library paths.
Coordinates are KiCad library units (mm, Y up).
"""
from sexp import Sym


def _font():
    return [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]]]


def _hidden_font():
    return [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]], Sym("hide")]


def _prop(name, value, x=0.0, y=0.0, hide=False):
    return [Sym("property"), name, value, [Sym("at"), x, y, 0], _hidden_font() if hide else _font()]


def _pin(etype, x, y, angle, name, number, length=2.54, hide_name=True):
    return [Sym("pin"), Sym(etype), Sym("line"), [Sym("at"), x, y, angle], [Sym("length"), length],
            [Sym("name"), name, _font()], [Sym("number"), number, _font()]]


def _rect(x0, y0, x1, y1):
    return [Sym("rectangle"), [Sym("start"), x0, y0], [Sym("end"), x1, y1],
            [Sym("stroke"), [Sym("width"), 0.254], [Sym("type"), Sym("default")]],
            [Sym("fill"), [Sym("type"), Sym("none")]]]


def _poly(pts, fill="none"):
    return [Sym("polyline"), [Sym("pts")] + [[Sym("xy"), x, y] for x, y in pts],
            [Sym("stroke"), [Sym("width"), 0.254], [Sym("type"), Sym("default")]],
            [Sym("fill"), [Sym("type"), Sym(fill)]]]


def _symbol(name, ref, graphics, pins, pin_names_hidden=True, power=False):
    node = [Sym("symbol"), f"bb:{name}"]
    if power:
        node.append([Sym("power")])
    node.append([Sym("pin_numbers"), Sym("hide")])
    node.append([Sym("pin_names"), [Sym("offset"), 0.254]] + ([Sym("hide")] if pin_names_hidden else []))
    node += [[Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("no" if power else "yes")],
             [Sym("on_board"), Sym("no" if power else "yes")]]
    node += [_prop("Reference", ref, 0, 3.81), _prop("Value", name, 0, -3.81),
             _prop("Footprint", "", 0, 0, True), _prop("Datasheet", "", 0, 0, True)]
    node.append([Sym("symbol"), f"{name}_0_1"] + graphics)
    node.append([Sym("symbol"), f"{name}_1_1"] + pins)
    return node


def two_pin(name, ref, graphics, etype="passive"):
    # vertical two-pin: pin 1 on top (connection at y=+3.81), pin 2 at bottom
    return _symbol(name, ref, graphics, [
        _pin(etype, 0, 3.81, 270, "1", "1", 1.27),
        _pin(etype, 0, -3.81, 90, "2", "2", 1.27),
    ])


GENERICS = {}


def _reg(name, node, pins):
    GENERICS[name] = {"node": node, "pins": pins}


def build():
    if GENERICS:
        return GENERICS
    # Resistor / capacitor / inductor / ferrite / fuse / NTC
    _reg("R", two_pin("R", "R", [_rect(-1.016, -2.54, 1.016, 2.54)]), ["1", "2"])
    _reg("C", two_pin("C", "C", [_poly([(-2.032, 0.762), (2.032, 0.762)]), _poly([(-2.032, -0.762), (2.032, -0.762)])]), ["1", "2"])
    _reg("L", two_pin("L", "L", [_rect(-1.016, -2.54, 1.016, 2.54), _poly([(-1.016, 0), (1.016, 0)])]), ["1", "2"])
    _reg("FB", two_pin("FB", "FB", [_rect(-1.27, -2.032, 1.27, 2.032), _poly([(-1.27, -2.032), (1.27, 2.032)])]), ["1", "2"])
    _reg("F", two_pin("F", "F", [_rect(-0.762, -2.54, 0.762, 2.54), _poly([(0, -2.54), (0, 2.54)])]), ["1", "2"])
    _reg("NTC", two_pin("NTC", "TH", [_rect(-1.016, -2.54, 1.016, 2.54), _poly([(-1.778, -1.778), (1.778, 1.778)])]), ["1", "2"])
    # Solder jumper / 0-ohm link drawn as a gap
    _reg("JP", two_pin("JP", "JP", [_poly([(-1.016, 1.016), (1.016, 1.016)]), _poly([(-1.016, -1.016), (1.016, -1.016)])]), ["1", "2"])
    # Diode-like: pin 1 = A (top), pin 2 = K (bottom)
    tri = [_poly([(-1.27, 1.27), (1.27, 1.27), (0, -1.27), (-1.27, 1.27)]), _poly([(-1.27, -1.27), (1.27, -1.27)])]
    _reg("D", _symbol("D", "D", tri, [_pin("passive", 0, 3.81, 270, "A", "1", 2.54), _pin("passive", 0, -3.81, 90, "K", "2", 2.54)]), ["A", "K"])
    _reg("TVS", _symbol("TVS", "D", tri + [_poly([(1.27, -1.27), (1.778, -0.762)])],
                        [_pin("passive", 0, 3.81, 270, "A", "1", 2.54), _pin("passive", 0, -3.81, 90, "K", "2", 2.54)]), ["A", "K"])
    _reg("LED", _symbol("LED", "D", tri + [_poly([(1.778, 0.508), (3.048, 1.778)])],
                        [_pin("passive", 0, 3.81, 270, "A", "1", 2.54), _pin("passive", 0, -3.81, 90, "K", "2", 2.54)]), ["A", "K"])
    # MOSFETs: G left, D top, S bottom (pin numbers follow the common SOT-23 G=1 S=2 D=3)
    body = [_rect(-1.27, -2.54, 1.778, 2.54)]
    _reg("NMOS", _symbol("NMOS", "Q", body, [
        _pin("input", -5.08, 0, 0, "G", "1", 3.81), _pin("passive", 0, -5.08, 90, "S", "2", 2.54),
        _pin("passive", 0, 5.08, 270, "D", "3", 2.54)]), ["G", "S", "D"])
    _reg("PMOS", _symbol("PMOS", "Q", body + [_poly([(-0.508, 0), (0.508, 0.508)])], [
        _pin("input", -5.08, 0, 0, "G", "1", 3.81), _pin("passive", 0, -5.08, 90, "S", "2", 2.54),
        _pin("passive", 0, 5.08, 270, "D", "3", 2.54)]), ["G", "S", "D"])
    # Power FET in 5x6 (S=1,2,3  G=4  D=5..8 + tab) mapped to one pin each; footprint pads share numbers
    _reg("NMOS_PWR", _symbol("NMOS_PWR", "Q", body, [
        _pin("input", -5.08, 0, 0, "G", "4", 3.81), _pin("passive", 0, -5.08, 90, "S", "1", 2.54),
        _pin("passive", 0, 5.08, 270, "D", "5", 2.54)]), ["G", "S", "D"])
    # Test point (single pin)
    _reg("TP", _symbol("TP", "TP", [_poly([(0, 0), (0, 1.27)]), [Sym("circle"), [Sym("center"), 0, 1.778], [Sym("radius"), 0.508],
                                     [Sym("stroke"), [Sym("width"), 0.254], [Sym("type"), Sym("default")]], [Sym("fill"), [Sym("type"), Sym("none")]]]],
                       [_pin("passive", 0, -2.54, 90, "1", "1", 2.54)]), ["1"])
    # Crystal, 4-pad (1 & 3 = crystal, 2 & 4 = case GND)
    _reg("XTAL4", _symbol("XTAL4", "Y", [_rect(-1.016, -1.778, 1.016, 1.778)], [
        _pin("passive", -5.08, 0, 0, "X1", "1", 3.81), _pin("passive", 5.08, 0, 180, "X2", "3", 3.81),
        _pin("passive", 0, -5.08, 90, "GND", "2", 2.54), _pin("passive", 0, 5.08, 270, "GND", "4", 2.54)]), ["X1", "X2", "GND"])
    # Push button / slide switch (2-pin), SPDT slide switch (3-pin)
    _reg("SW", two_pin("SW", "SW", [_poly([(-1.27, 1.778), (1.27, -1.016)])]), ["1", "2"])
    _reg("SW_SPDT", _symbol("SW_SPDT", "SW", [_poly([(0, 0), (2.54, 1.27)])], [
        _pin("passive", -5.08, 0, 0, "C", "2", 5.08), _pin("passive", 5.08, 2.54, 180, "A", "1", 2.54),
        _pin("passive", 5.08, -2.54, 180, "B", "3", 2.54)]), ["C", "A", "B"])
    return GENERICS


def connector(name, pin_names):
    """Generic N-pin connector symbol (pins on the left)."""
    n = len(pin_names)
    h = (n + 1) * 2.54
    pins = [_pin("passive", -7.62, h / 2 - 2.54 * (i + 1), 0, pn, str(i + 1), 2.54) for i, pn in enumerate(pin_names)]
    node = _symbol(name, "J", [_rect(-5.08, -h / 2, 5.08, h / 2)], pins, pin_names_hidden=False)
    return {"node": node, "pins": pin_names}
