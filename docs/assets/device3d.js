/* Battery Bank: interactive 3D model (docs/assets/device3d.js)
 * Built procedurally from mech_spec.json. Units mm; origin = front-left-bottom of the enclosure
 * interior; +X length, +Y front->back, +Z up. Do not hand-edit coordinates here: edit
 * hardware/mechanical/mech_spec.json, then run docs/assets/sync_mech_spec.py (it refreshes
 * docs/assets/mech_spec.json and the inline fallback below).
 * Values that are not in the spec (connector body depths, small-part sizes, the B2B header
 * orientation) are marked "assumed" and only affect looks, never the spec'd positions. */

const THREE_URL = 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
const ORBIT_URL = 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js';
let THREE, OrbitControls;

const FALLBACK_SPEC = /*SPEC-BEGIN*/{"_comment":"Single source of truth for mechanical layout. Units: mm. ONE frame for everything: origin = interior floor, front-left corner of the INTERIOR (inside the walls and the left end cap). +X along the length (left->right), +Y front->back, +Z up. Interior = 142 x 90 x 66. Board-local coordinates: origin at the board's front-left corner, top view, +X right, +Y toward the back edge; a board's 'position' is where its local origin sits in the interior frame. The PCB layout (KiCad) and the website 3D model both read this file. Rev B, 2026-11-21: fixes the 14 inconsistencies found by the 3D model build and applies the review-round-1 board partition (H-3).","rev":"B","changes_from_rev_A":["One coordinate frame (interior); all centres re-derived (rev A mixed outer/interior centres).","Partition: RTL8372N switch + NICs on board A; RTL8221B PHY + RJ45 + PoE + router + radios + audio + Qi + glow on board B; DC jacks stay on A.","Boards widened to 89 mm (0.5 mm from the inner walls) so edge connectors reach the wall; boards slide into extrusion card-guide slots (no standoffs over the cartridge).","Z stack re-planned: cartridge 0-25, board A at 30 (5 mm gap for THT leads), board B at 47, Qi coil and speaker under the top wall clear of board B's height limits.","Board B shortened to 96 mm so a 30x30x10 fan stands vertically at the right end, aligned with the back-face grille.","Cells side by side along X with axes along Y (105.5 x 70.2 fits the 112 x 82 cartridge).","Left end cap lengthened to 16 mm for a 20 mm TIR optic; Qi window and speaker no longer overlap."],"enclosure":{"type":"extruded aluminium body with two PC/ABS end caps; boards ride in card-guide slots in the extrusion","outer":{"length":150.0,"width":94.0,"height":70.0},"wall":2.0,"corner_radius":6.0,"interior":{"length":142.0,"width":90.0,"height":66.0},"end_caps":{"left":{"length":6.0,"outer_length":6.0,"note":"interior starts after the 4 mm cap wall + optic recess; see led board","material":"PC, RF-transparent","contains":["flashlight 20 mm TIR optic","red night LED","Wi-Fi/BLE FPC antennas (RF window)","LoRa SMA bulkhead"]},"right":{"material":"ABS","contains":["battery cartridge door (top-hinged)","cartridge latch"]}},"outer_to_interior_offset":{"x":4.0,"y":2.0,"z":2.0},"top_window":{"material":"PC/glass, non-metal (Qi)","center_x":78.0,"center_y":45.0,"size_x":56.0,"size_y":56.0},"speaker_grille":{"face":"top","center_x":26.0,"center_y":45.0,"diameter":40.0},"glow_strip":{"edge":"front-top","x0":12.0,"x1":130.0,"z_center":56.0,"height":3.0,"note":"light pipe on the flat front face (flat face spans z 4..60 interior)"},"fan_grille":{"face":"back","center_x":124.0,"center_z":46.0,"size":30.0},"tripod_insert":{"face":"bottom","thread":"1/4-20 UNC","center_x":71.0,"center_y":45.0}},"cartridge":{"cells":"5S1P Samsung 50S 21700 (21.1 dia x 70.2 mm): 5 cells side by side along X (pitch 21.1), axes along Y","outer":{"length":112.0,"width":82.0,"height":25.0},"position":{"x":26.0,"y":4.0,"z":0.0},"inserts_from":"right end cap (+X); slides along X","connector":{"type":"XT60PW + 5 pogo pads (GND, SDA, SCL, PRES_A, PRES_B)","mates_at_x":26.0,"note":"blind-mate at the inner (left) end of the bay, on a bracket under board A"},"energy_wh":90},"boards":[{"id":"power","name":"Power board (A)","outline":{"x":141.0,"y":89.0,"corner_radius":2.0},"thickness":1.6,"layers":6,"copper_outer_oz":2,"copper_inner_oz":1,"finish":"ENIG","mask":"matte black","position":{"x":0.5,"y":0.5,"z":30.0},"mounting":"card-guide slots along both long edges (1.5 mm engagement) + 2 screws into end-cap bosses at x 3 and x 138 on the centre line","assembly":"SMT top side only + THT connectors","max_component_height_top":14.0,"contents":["4x USB-C port stages (BQ25756 + TPS26750 + TPD4S480 + HD3SS3212 + RTL8156BG + 0.95 V buck)","RTL8372N switch + flash + core buck","input stage (DC jack eFuse + ORing + BQ25756)","DC-out stage","aux rails","USB-A","battery interface + bus","ESP32 + I2C mux/expanders + RTC + microSD","flashlight driver","fan (stands at the right end, see external_parts)"],"edge_connectors":[{"ref":"J_USBC1","type":"USB-C 24p mid-mount","edge":"front","x":22.0,"w":9.0,"h":3.3},{"ref":"J_USBC2","type":"USB-C 24p mid-mount","edge":"front","x":38.0,"w":9.0,"h":3.3},{"ref":"J_USBC3","type":"USB-C 24p mid-mount","edge":"front","x":54.0,"w":9.0,"h":3.3},{"ref":"J_USBC4","type":"USB-C 24p mid-mount","edge":"front","x":70.0,"w":9.0,"h":3.3},{"ref":"J_USBA","type":"USB-A THT","edge":"front","x":88.0,"w":13.2,"h":5.8},{"ref":"J_MICROSD","type":"microSD push-push","edge":"front","x":104.0,"w":14.0,"h":1.9},{"ref":"SW_SLOW","type":"slide switch","edge":"front","x":118.0,"w":9.1,"h":3.5},{"ref":"SW_FLASH","type":"tactile button (light-pipe cap)","edge":"front","x":128.0,"w":5.1,"h":5.1},{"ref":"SW_BOOT","type":"tactile button (recessed)","edge":"front","x":135.0,"w":5.1,"h":5.1},{"ref":"J_DCIN","type":"DC barrel 2.0 mm (input)","edge":"back","x":64.0,"w":9.0,"h":11.0},{"ref":"J_DCOUT","type":"DC barrel 2.5 mm (output)","edge":"back","x":80.0,"w":9.0,"h":11.0},{"ref":"J_LEDHARNESS","type":"JST PH 6p to the LED board","edge":"left","y":44.5,"w":13.9,"h":6.0}],"zones":[{"name":"USB-C port stages x4 (17x17 inductor each)","x0":4.0,"y0":6.0,"x1":80.0,"y1":50.0},{"name":"4x RTL8156BG NICs + RTL8372N switch (MDI inner stripline < 50 mm)","x0":4.0,"y0":50.0,"x1":56.0,"y1":70.0},{"name":"Input + DC-out stages","x0":56.0,"y0":50.0,"x1":98.0,"y1":70.0},{"name":"B2B strip (2x24 2.54 mm low-speed/power + HS mezzanine), mirrored on board B","x0":30.0,"y0":72.0,"x1":96.0,"y1":80.0},{"name":"DC jacks + their eFuses","x0":56.0,"y0":80.0,"x1":98.0,"y1":88.5},{"name":"Aux rails, USB-A, ESP32, microSD","x0":80.0,"y0":6.0,"x1":134.0,"y1":56.0},{"name":"Fan keep-out (fan stands here)","x0":102.0,"y0":74.0,"x1":134.0,"y1":88.5}],"board_to_board":[{"name":"low-speed + power","type":"2x24 2.54 mm stacking header (A) / socket (B)","stack_height":15.4,"x":33.0,"y":76.0,"orientation":"along X (61 mm)"},{"name":"SerDes mezzanine","type":"differential-rated mezzanine, G-S-S-G, 13+ pins","stack_height":15.4,"x":30.0,"y":73.0,"orientation":"along X; place nearest the switch"}]},{"id":"logic","name":"Logic / network board (B)","outline":{"x":96.0,"y":89.0,"corner_radius":2.0},"thickness":1.6,"layers":6,"copper_outer_oz":1,"copper_inner_oz":1,"finish":"ENIG","mask":"matte black","position":{"x":0.5,"y":0.5,"z":47.0},"mounting":"card-guide slots + B2B headers; screw boss at the left end","assembly":"SMT top side only + THT RJ45","max_component_height_top":12.0,"height_keepouts":[{"name":"under speaker (max 3.5 mm)","x0":6.0,"y0":25.0,"x1":46.0,"y1":65.0,"max_height":3.5},{"name":"under Qi coil (max 12 mm; coil sits above)","x0":53.0,"y0":20.0,"x1":96.0,"y1":70.0,"max_height":12.0}],"contents":["router module","RTL8221B PHY + RJ45 + PoE PD + isolated flyback","LoRa node","audio amp + mics","Qi transmitter","glow strip feed","NFC"],"edge_connectors":[{"ref":"J_RJ45","type":"RJ45 2.5GBASE-T + PoE (bt)","edge":"back","x":22.0,"w":16.0,"h":13.5}],"zones":[{"name":"RJ45 + RTL8221B + PoE PD + isolated flyback","x0":2.0,"y0":30.0,"x1":30.0,"y1":88.5},{"name":"Router module","x0":52.0,"y0":30.0,"x1":95.0,"y1":72.0},{"name":"B2B strip (mates board A)","x0":30.0,"y0":72.0,"x1":96.0,"y1":80.0},{"name":"LoRa node","x0":2.0,"y0":2.0,"x1":30.0,"y1":28.0},{"name":"Audio amp + mics + NFC","x0":30.0,"y0":2.0,"x1":52.0,"y1":70.0},{"name":"Qi transmitter (under the coil, max 12 mm)","x0":52.0,"y0":2.0,"x1":95.0,"y1":30.0}]},{"id":"led","name":"LED board (aluminium core)","outline":{"x":24.0,"y":24.0,"corner_radius":12.0},"thickness":1.6,"layers":1,"finish":"HASL","mask":"white","position":{"x":-4.0,"y":33.0,"z":32.0},"orientation":"faces -X into the 20 mm TIR optic in the left end cap","parts":["Cree XP-G3 5700 K","red night LED","10k NTC"]}],"external_parts":[{"name":"Fan 30x30x10 (vertical, blowing out the back grille)","size":[30,10,30],"position":{"x":109.0,"y":79.0,"z":32.0},"note":"x/y/z = min corner; axis along +Y; spans z 32-62, above board A (top 31.6) and right of board B (ends x 96.5)"},{"name":"Speaker 40 mm 4 ohm","diameter":40,"depth":7.4,"position":{"x":26.0,"y":45.0,"z":58.4},"note":"centre x/y; z = bottom; top at 65.8 under the 66 mm interior top"},{"name":"Qi coil A11 (50 mm) + ferrite","diameter":50,"depth":3.0,"position":{"x":78.0,"y":45.0,"z":62.8},"note":"centre x/y; z = bottom; top at 65.8"},{"name":"Glow light pipe + 8x SK6812MINI-E","position":"front-top edge, fed from board B"}],"notes":["All positions are pre-layout estimates; the layout must keep the edge-connector positions and the z stack.","Board B ends at x 96.5; the fan and the right end cap door path occupy x 102-142 above board A."]}/*SPEC-END*/;

/* ------------------------------------------------------------------ layout (pure, no DOM) */
const num = (s, re, d) => { const m = re.exec(s || ''); return m ? parseFloat(m[1]) : d; };
// assumed connector body depths (mm, into the board from the mouth); not in the spec
const DEPTH = [[/USB-C/i, 7.35], [/USB-A/i, 14], [/barrel/i, 14], [/RJ45/i, 21], [/microSD/i, 15], [/slide/i, 4.5], [/tactile/i, 3.8], [/JST/i, 6]];
const box6 = (a) => ({ x0: a[0], y0: a[1], z0: a[2], x1: a[3], y1: a[4], z1: a[5] });
const arr = (v) => (Array.isArray(v) ? v : v ? [v] : []);

export function layout(S) {
  const E = S.enclosure, o = E.outer, w = E.wall, r = E.corner_radius, notes = [];
  const off = E.outer_to_interior_offset || { x: w, y: w, z: w }; // rev A had no offset: interior = outer - wall
  const out = box6([-off.x, -off.y, -off.z, o.length - off.x, o.width - off.y, o.height - off.z]);
  const I = E.interior || {}, inn = { x: I.length || o.length - 2 * off.x, y: I.width || o.width - 2 * off.y, z: I.height || o.height - 2 * off.z };
  const L = { S, E, out, inn, r, w, notes, rows: [] };
  const row = (id, b, src) => L.rows.push({ id, ...b, src });
  const ec = E.end_caps || {}, lc = ec.left || {}, rc = ec.right || {};
  const capLen = (c, other) => c.outer_length ?? c.length ?? E.end_cap_length ?? other;
  const cl = capLen(lc, 12), cr = capLen(rc, null) ?? cl;
  if (capLen(rc, null) == null) notes.push(`end_caps.right has no length; drawn ${cr} mm (same as the left cap)`);
  L.capL = { x0: out.x0, x1: out.x0 + cl }; L.capR = { x0: out.x1 - cr, x1: out.x1 }; L.body = { x0: L.capL.x1, x1: L.capR.x0 };
  if (E.body_length && Math.abs(E.body_length - (L.body.x1 - L.body.x0)) > 0.01) notes.push(`body_length ${E.body_length} != outer length - caps`);
  row('body', { ...out, x0: L.body.x0, x1: L.body.x1 }, 'enclosure.outer - end caps');
  row('cap L', { ...out, x0: L.capL.x0, x1: L.capL.x1 }, 'end_caps.left.outer_length');
  row('cap R', { ...out, x0: L.capR.x0, x1: L.capR.x1 }, 'end_caps.right (length assumed if absent)');
  const flat = { z0: out.z0 + r, z1: out.z1 - r };
  const tw = E.top_window; L.win = { cx: tw.center_x, cy: tw.center_y, sx: tw.size_x, sy: tw.size_y };
  row('Qi window', box6([tw.center_x - tw.size_x / 2, tw.center_y - tw.size_y / 2, out.z1, tw.center_x + tw.size_x / 2, tw.center_y + tw.size_y / 2, out.z1]), 'top_window');
  const sg = E.speaker_grille; L.spkG = { cx: sg.center_x, cy: sg.center_y, rad: sg.diameter / 2 };
  row('speaker grille', box6([sg.center_x - sg.diameter / 2, sg.center_y - sg.diameter / 2, out.z1, sg.center_x + sg.diameter / 2, sg.center_y + sg.diameter / 2, out.z1]), 'speaker_grille');
  const fg = E.fan_grille; L.fanG = { cx: fg.center_x, cz: fg.center_z, s: fg.size, zFlat: flat.z1, zLow: flat.z0 };
  row('fan grille', box6([fg.center_x - fg.size / 2, out.y1, fg.center_z - fg.size / 2, fg.center_x + fg.size / 2, out.y1, fg.center_z + fg.size / 2]), 'fan_grille');
  const gs = E.glow_strip, gz = gs.z_center ?? flat.z1 - gs.height / 2;
  L.glow = { x0: gs.x0, x1: gs.x1, z0: gz - gs.height / 2, z1: gz + gs.height / 2 };
  row('glow strip', box6([gs.x0, out.y0, L.glow.z0, gs.x1, out.y0, L.glow.z1]), gs.z_center != null ? 'glow_strip' : 'glow_strip (z derived: top of flat front face)');
  L.flat = flat;
  const ti = E.tripod_insert; L.tripod = { cx: ti.center_x, cy: ti.center_y, r: /1\/4/.test(ti.thread) ? 3.175 : 3 };

  // cartridge + cells
  const C = S.cartridge, co = C.outer, cp = C.position;
  const cart = L.cart = { ...box6([cp.x, cp.y, cp.z, cp.x + co.length, cp.y + co.width, cp.z + co.height]), cells: [], C };
  row('cartridge', cart, 'cartridge.position/outer');
  const d = num(C.cells, /([\d.]+)\s*(?:mm\s*)?(?:dia\s*)?x\s*[\d.]+\s*mm/i, 21.1), len = num(C.cells, /[\d.]+\s*(?:mm\s*)?(?:dia\s*)?x\s*([\d.]+)\s*mm/i, 70.2);
  const sp = /(\d+)S(\d+)P/i.exec(C.cells || ''), n = sp ? sp[1] * sp[2] : 5;
  const fitY = n * d <= co.width && len <= co.length, fitX = n * d <= co.length && len <= co.width;
  const dir = (/side by side along ([XY])/i.exec(C.cells || '') || [])[1];
  const alongY = dir ? dir.toUpperCase() === 'Y' : !fitX && fitY;
  if ((alongY && !fitY) || (!alongY && !fitX)) notes.push(`cartridge: ${n} x ${d} mm cells side by side along ${alongY ? 'Y' : 'X'} need ${(n * d).toFixed(1)} mm, cartridge is ${alongY ? co.width : co.length} mm`);
  for (let i = 0; i < n; i++) {
    const c = alongY ? { axis: 'x', cx: cart.x0 + co.length / 2, cy: cart.y0 + (co.width - n * d) / 2 + d * (i + 0.5) }
                     : { axis: 'y', cx: cart.x0 + (co.length - n * d) / 2 + d * (i + 0.5), cy: cart.y0 + co.width / 2 };
    cart.cells.push({ ...c, cz: cart.z0 + co.height / 2, r: d / 2, len });
    row(`cell ${i + 1}`, c.axis === 'y' ? box6([c.cx - d / 2, c.cy - len / 2, cart.z0 + co.height / 2 - d / 2, c.cx + d / 2, c.cy + len / 2, cart.z0 + co.height / 2 + d / 2]) : box6([c.cx - len / 2, c.cy - d / 2, cart.z0 + co.height / 2 - d / 2, c.cx + len / 2, c.cy + d / 2, cart.z0 + co.height / 2 + d / 2]), 'cartridge.cells (centred in the cartridge)');
  }
  cart.alongY = alongY;
  if (d > co.height) notes.push(`cartridge: cell diameter ${d} > cartridge height ${co.height}`);
  cart.mate = C.connector && C.connector.mates_at_x;
  cart.pogo = num(C.connector && C.connector.type, /(\d+)\s*pogo/i, 4);

  // boards
  L.boards = []; L.ext = []; L.hdrs = []; L.bosses = [];
  for (const b of S.boards) {
    const p = b.position, W = b.outline.x, H = b.outline.y, t = b.thickness;
    if (/[-+]X/.test(b.orientation || '')) {
      L.led = { ...b, ...box6([p.x, p.y, p.z, p.x + t, p.y + W, p.z + H]), W, H, t };
      row(b.name, L.led, `boards[${b.id}] (vertical, faces -X: local x->+Y, y->+Z)`);
      continue;
    }
    const ov = { front: p.y, back: inn.y - (p.y + H), left: p.x, right: inn.x - (p.x + W) };
    const conns = (b.edge_connectors || []).map((c) => {
      const dep = (DEPTH.find(([re]) => re.test(c.type)) || [0, 8])[1], e = c.edge;
      const mid = /mid-mount/i.test(c.type), front = e === 'front', side = e === 'left' || e === 'right';
      const zc = mid ? t / 2 : t + c.h / 2;
      // local frame: mouth point (mx,my), facing direction; footprint rect fx0..fx1, fy0..fy1 (board-local)
      const k = side ? { mx: e === 'left' ? -ov.left : W + ov.right, my: c.y, rot: e === 'left' ? Math.PI / 2 : -Math.PI / 2 }
                     : { mx: c.x, my: front ? -ov.front : H + ov.back, rot: front ? Math.PI : 0 };
      const f = side ? { fx0: e === 'left' ? k.mx : k.mx - dep, fy0: c.y - c.w / 2, fw: dep, fd: c.w } : { fx0: c.x - c.w / 2, fy0: front ? k.my : k.my - dep, fw: c.w, fd: dep };
      return { ...c, d: dep, mid, front, side, zc, ...k, ...f };
    });
    const ko = arr(b.height_keepouts).map((q) => ({ ...q }));
    const B = { ...b, p, W, H, t, conns, ko, top: p.z + t, maxH: b.max_component_height_top || 0 };
    L.boards.push(B);
    row(b.name, box6([p.x, p.y, p.z, p.x + W, p.y + H, p.z + t]), `boards[${b.id}].position/outline`);
    for (const c of conns) row(c.ref, box6([p.x + c.fx0, p.y + c.fy0, p.z + c.zc - c.h / 2, p.x + c.fx0 + c.fw, p.y + c.fy0 + c.fd, p.z + c.zc + c.h / 2]), `${b.id}.edge_connectors (depth assumed ${c.d})`);
    for (const q of ko) row(`keepout ${b.id}: ${q.name}`, box6([p.x + q.x0, p.y + q.y0, p.z + t + q.max_height, p.x + q.x1, p.y + q.y1, p.z + t + B.maxH]), `${b.id}.height_keepouts (board-local)`);
    // screws into end-cap bosses ("... bosses at x 3 and x 138 on the centre line")
    const mnt = b.mounting || '', bx = /boss/i.test(mnt) ? [...mnt.matchAll(/x\s*([\d.]+)/g)].map((m) => +m[1]) : [];
    for (const x of bx) { L.bosses.push({ board: b.id, x, y: H / 2 }); row(`screw boss ${b.id} x${x}`, box6([p.x + x - 3, p.y + H / 2 - 3, p.z - 4, p.x + x + 3, p.y + H / 2 + 3, p.z]), `${b.id}.mounting (boss size assumed 6x6x4)`); }
    if (/boss/i.test(mnt) && !bx.length) notes.push(`${b.id}: "${mnt}" gives no boss position; not drawn`);
    B.rails = /card-guide/i.test(mnt) || /card-guide/i.test(E.type || '') ? num(mnt, /([\d.]+)\s*mm engagement/i, 1.5) : 0;
  }
  // board-to-board connectors (object or list; x = left end, y = centreline, along X)
  for (const b of L.boards) for (const h of arr(b.board_to_board)) {
    const st = h.stack_height ?? h.height, m = /(\d+)\s*x\s*(\d+)/i.exec(h.type || ''), pitch = num(h.type, /([\d.]+)\s*mm/, 1.27);
    const rows = m ? +m[1] : 0, cols = m ? +m[2] : 0;
    const lw = num(h.orientation, /\(([\d.]+)\s*mm\)/, cols ? cols * pitch + (h.stack_height ? 0 : 2) : 12), ld = rows ? rows * pitch + (h.stack_height ? 0 : 2) : 4;
    const other = L.boards.find((q) => q !== b && (Math.abs(q.p.z - (b.top + st)) < 0.05 || Math.abs(q.top - (b.p.z - st)) < 0.05));
    if (!other) notes.push(`B2B "${h.name || h.type}" stack ${st} mm does not bridge to another board`);
    const lower = other && other.p.z < b.p.z ? other : b, upper = lower === b ? other : b;
    const centred = !h.stack_height; // rev A gave the header centre
    const lx0 = centred ? h.x - lw / 2 : h.x, ly0 = h.y - ld / 2;
    const hd = { ...h, rows, cols, pitch, lx0, ly0, lw, ld, lower: lower.id, upper: upper && upper.id, z0: lower.top, z1: lower.top + st, wx: b.p.x, wy: b.p.y, mezz: !m };
    L.hdrs.push(hd);
    row(`B2B ${h.name || 'header'}`, box6([b.p.x + lx0, b.p.y + ly0, hd.z0, b.p.x + lx0 + lw, b.p.y + ly0 + ld, hd.z1]), `${b.id}.board_to_board (${m ? '' : 'footprint assumed ' + lw + 'x' + ld + ', '}x = ${centred ? 'centre' : 'left end'}, y = centreline)`);
  }
  // external parts
  const fit = (v, s, hi, ax, nm) => {
    if (v >= 0 && v + s <= hi) return [v, v + s];
    if (v - s / 2 >= 0 && v + s / 2 <= hi) { notes.push(`${nm}: position.${ax}=${v} as a min corner ends at ${v + s} > interior ${hi}; read as a centre instead`); return [v - s / 2, v + s / 2]; }
    notes.push(`${nm}: does not fit along ${ax}`); return [v, v + s];
  };
  for (const e of S.external_parts || []) {
    const p = e.position;
    if (/^fan/i.test(e.name) && e.size) {
      const [x0, x1] = fit(p.x, e.size[0], inn.x, 'x', e.name), [y0, y1] = fit(p.y, e.size[1], inn.y, 'y', e.name), [z0, z1] = fit(p.z, e.size[2], inn.z, 'z', e.name);
      const axis = 'xyz'[e.size.indexOf(Math.min(...e.size))];
      L.fan = { ...box6([x0, y0, z0, x1, y1, z1]), name: e.name, size: e.size, axis };
      L.ext.push(L.fan); row('fan', L.fan, `external_parts.Fan (min corner, axis ${axis})`);
    } else if (e.diameter && typeof p === 'object') {
      const c = { name: e.name, cx: p.x, cy: p.y, rad: e.diameter / 2, ...box6([p.x - e.diameter / 2, p.y - e.diameter / 2, p.z, p.x + e.diameter / 2, p.y + e.diameter / 2, p.z + e.depth]) };
      if (/speaker/i.test(e.name)) L.spk = c; else if (/qi|coil/i.test(e.name)) L.coil = c;
      L.ext.push(c); row(/speaker/i.test(e.name) ? 'speaker' : 'Qi coil', c, `external_parts.${e.name} (x,y = centre, z = bottom)`);
    } else if (/glow/i.test(e.name)) L.glowLeds = num(e.name, /(\d+)\s*x/i, 8);
  }
  return L;
}

// assumed small-part kits per zone: [kind, w, d, h, count, label]
const ESP = [['mod', 18, 19.2, 3.2, 1, 'ESP32-WROOM-32UE'], ['ic', 7.8, 4.4, 1.1, 1, 'TCA9548A I2C mux'], ['ic', 4, 4, 0.9, 1, 'I/O expander'], ['ic', 3.2, 1.5, 0.8, 1, 'RV-3028 RTC'], ['ic', 2.9, 1.6, 1.1, 2, 'level shifter'], ['conn', 3, 3, 1.2, 1, 'U.FL']];
const KIT = {
  input: [['ind', 17, 17, 8, 2, '17x17 power inductor'], ['ic', 6, 5, 0.9, 2, 'BQ25756 buck-boost'], ['ic', 5, 6, 1, 8, '100 V power FET'], ['res', 6.3, 3.2, 0.6, 4, '5 mOhm 2512 sense'], ['can', 6.3, 6.3, 5.8, 2, 'polymer bulk cap'], ['ic', 5, 5, 0.9, 1, 'ORing controller'], ['mlcc', 3.2, 1.6, 1.4, 8, 'MLCC 1206']],
  aux: [['ind', 10, 10, 5, 1, 'aux buck inductor (12 V)'], ['ind', 7, 7, 4.5, 3, 'aux buck inductor'], ['ic', 3, 3, 0.8, 3, 'aux buck'], ['ic', 5, 4, 1.5, 1, 'IP6525S USB-A'], ['ic', 2, 2, 0.8, 3, 'TPS22965 load switch'], ['ic', 3, 3, 0.8, 1, 'AL8860 flashlight driver'], ['res', 6.3, 3.2, 0.6, 2, '2512 sense'], ['mlcc', 2, 1.25, 1.1, 14, 'MLCC 0805']],
  esp: ESP.concat([['ic', 3, 3, 0.8, 1, 'MAX98357A amp'], ['ic', 3.5, 2.65, 1, 1, 'PDM mic'], ['ic', 1.6, 1.6, 0.5, 1, 'NT3H2111 NFC'], ['mlcc', 2, 1.25, 1.1, 10, 'MLCC 0805']]),
  esp2: ESP.concat([['mlcc', 2, 1.25, 1.1, 8, 'MLCC 0805']]),
  nic: [['ic', 11, 11, 1, 1, 'RTL8372N 2.5G switch'], ['ic', 6, 6, 0.9, 4, 'RTL8156BG 2.5G NIC'], ['ic', 5, 4, 1.5, 1, 'SPI flash'], ['ind', 5, 5, 3, 1, 'core buck inductor'], ['ic', 3.2, 2.5, 0.8, 2, '25 MHz crystal'], ['mlcc', 2, 1.25, 1.1, 12, 'MLCC 0805']],
  jack: [['ic', 6.5, 4.4, 1, 2, 'TPS26631 eFuse'], ['ic', 4.6, 3.9, 2.2, 2, 'TVS diode'], ['mlcc', 3.2, 1.6, 1.4, 6, 'MLCC 1206']],
  sw: [['xfmr', 14, 12, 10, 1, 'PoE flyback transformer'], ['ic', 11, 11, 1, 1, 'RTL8372N 2.5G switch'], ['ic', 6, 6, 0.9, 1, 'RTL8221B 2.5G PHY'], ['ic', 5, 5, 0.9, 1, 'PoE PD controller'], ['can', 8, 8, 6, 2, 'bulk cap'], ['ind', 5, 5, 3, 2, 'buck inductor'], ['ic', 4.6, 3.9, 2.2, 2, 'bridge rectifier'], ['ic', 3.2, 2.5, 0.8, 2, '25 MHz crystal'], ['mlcc', 2, 1.25, 1.1, 12, 'MLCC 0805']],
  phy: [['xfmr', 14, 12, 10, 1, 'PoE flyback transformer'], ['ic', 6, 6, 0.9, 1, 'RTL8221B 2.5G PHY'], ['ic', 5, 5, 0.9, 1, 'PoE PD controller'], ['can', 8, 8, 6, 2, 'bulk cap'], ['ind', 5, 5, 3, 2, 'buck inductor'], ['ic', 4.6, 3.9, 2.2, 2, 'bridge rectifier'], ['ic', 3.2, 2.5, 0.8, 1, '25 MHz crystal'], ['mlcc', 2, 1.25, 1.1, 10, 'MLCC 0805']],
  router: [['mod', 50, 36, 3.4, 1, 'Acelink SM81 router module (MT7981B)']],
  lora: [['mod', 14, 20, 2.4, 1, 'E22-900M22S (SX1262)'], ['mod', 13, 18, 2.2, 1, 'E73-2G4M08S1CX (nRF52840)'], ['conn', 3, 3, 1.2, 2, 'IPEX antenna']],
  audio: [['ic', 3, 3, 0.8, 1, 'MAX98357A amp'], ['ic', 3.5, 2.65, 1, 2, 'PDM mic'], ['ic', 1.6, 1.6, 0.5, 1, 'NT3H2111 NFC'], ['ic', 2.9, 1.6, 1.1, 2, 'level shifter'], ['mlcc', 2, 1.25, 1.1, 8, 'MLCC 0805']],
  qi: [['ind', 10, 10, 5, 1, '12 V Qi buck inductor'], ['ic', 5, 5, 0.9, 1, 'IP6826 Qi transmitter'], ['ic', 3, 3, 0.8, 1, '12 V buck'], ['can', 6.3, 6.3, 5.8, 2, 'polymer bulk cap'], ['ic', 3.2, 2.5, 1, 2, 'full-bridge FET'], ['mlcc', 2, 1.25, 1.1, 8, 'MLCC 0805']],
};
// first match wins for the "family"; ESP32 adds its kit to any zone that names it
const ZONEKIT = [[/B2B|keep-out/i, null], [/USB-C port/i, 'usb'], [/DC jacks/i, 'jack'], [/Input/i, 'input'], [/NIC|RTL8372/i, 'nic'], [/RJ45|RTL8221B|PoE/i, 'phy'], [/Fan/i, null], [/Router/i, 'router'], [/LoRa/i, 'lora'], [/Audio/i, 'audio'], [/Qi/i, 'qi'], [/Aux/i, 'aux'], [/ESP32/i, 'esp']];

export function populate(L, b) {
  const occ = [], parts = [], miss = [], G = 0.5;
  const hit = (x, y, w, d, h) => occ.some((o) => x < o.x1 + G && x + w > o.x0 - G && y < o.y1 + G && y + d > o.y0 - G && h > o.zmin);
  const take = (x, y, w, d, zmin = 0) => occ.push({ x0: x, y0: y, x1: x + w, y1: y + d, zmin });
  for (const c of b.conns) take(c.fx0, c.fy0, c.fw, c.fd);
  for (const h of b.mounting_holes || []) take(h.x - h.d / 2 - 1.6, h.y - h.d / 2 - 1.6, h.d + 3.2, h.d + 3.2);
  for (const s of L.bosses) if (s.board === b.id) take(s.x - 3.5, s.y - 3.5, 7, 7);
  for (const H of L.hdrs) if (H.upper === b.id || H.lower === b.id) take(H.lx0, H.ly0, H.lw, H.ld);
  for (const q of b.ko) take(q.x0, q.y0, q.x1 - q.x0, q.y1 - q.y0, q.max_height);
  for (const e of L.ext) { // external parts that sit inside this board's component envelope
    const zmin = e.z0 - b.top;
    if (zmin >= -0.5 && zmin < b.maxH && e.x1 > b.p.x && e.x0 < b.p.x + b.W && e.y1 > b.p.y && e.y0 < b.p.y + b.H) take(e.x0 - b.p.x, e.y0 - b.p.y, e.x1 - e.x0, e.y1 - e.y0, Math.max(0, zmin));
  }
  const put = (k, x, y, w, d, h, label, zone) => { parts.push({ k, x, y, w, d, h, label, zone: zone.name }); take(x, y, w, d); };
  const scan = (k, w, d, h, label, z) => { for (let y = z.y0 + G / 2; y + d <= z.y1 - G / 2 + 1e-6; y += 0.5) for (let x = z.x0 + G / 2; x + w <= z.x1 - G / 2 + 1e-6; x += 0.5) if (x >= 0.5 && y >= 0.5 && x + w <= b.W - 0.5 && y + d <= b.H - 0.5 && !hit(x, y, w, d, h)) { put(k, x, y, w, d, h, label, z); return true; } return false; };
  const place = (k, w, d, h, label, zs) => {
    for (const z of zs) for (const [pw, pd] of w === d ? [[w, d]] : [[w, d], [d, w]]) if (scan(k, pw, pd, h, label, z)) { if (z !== zs[0]) miss.push(`${label}: no room in "${zs[0].name}", placed in "${z.name}"`); return true; }
    miss.push(`${label} (${w}x${d}) does not fit in "${zs[0].name}"`);
    if (k === 'mod') { const z = zs[0], x = Math.max(0.5, Math.min(b.W - 0.5 - w, (z.x0 + z.x1 - w) / 2)), y = Math.max(0.5, Math.min(b.H - 0.5 - d, (z.y0 + z.y1 - d) / 2)); put(k, x, y, w, d, h, `${label} (overflows its zone)`, z); }
    return false;
  };
  const zones = (b.zones || []).slice().sort((p, q) => (p.x1 - p.x0) * (p.y1 - p.y0) - (q.x1 - q.x0) * (q.y1 - q.y0));
  for (const z of zones) {
    const fam = ZONEKIT.find(([re]) => re.test(z.name)), kit = fam ? fam[1] : 'aux';
    const kits = kit ? [kit] : [];
    if (kit && kit !== 'esp' && /ESP32/i.test(z.name)) kits.push('esp2');
    const zs = [z, ...zones.filter((q) => q !== z && q.x0 <= z.x0 && q.y0 <= z.y0 && q.x1 >= z.x1 && q.y1 >= z.y1)];
    if (kit === 'usb') { // repeated port stage, hand-placed per column
      const n = num(z.name, /x\s*(\d+)/i, 4), cw = (z.x1 - z.x0) / n, y0 = z.y0;
      for (let i = 0; i < n; i++) {
        const cx = z.x0 + cw * (i + 0.5);
        const S = [['ind', cx - 8.5, z.y1 - 17 - G / 2, 17, 17, 8, '17x17 power inductor'], ['ic', cx - 6.5, y0 + 0.5, 3, 3, 0.75, 'TPD4S480 CC/SBU protector'], ['ic', cx + 1.5, y0 + 0.2, 4, 4, 0.9, 'TPS26750 PD controller'],
          ['ic', cx - 6, y0 + 5, 5, 6, 1, '100 V power FET'], ['ic', cx + 1, y0 + 5, 5, 6, 1, '100 V power FET'], ['ic', cx - 6, y0 + 11.5, 5, 6, 1, '100 V power FET'], ['ic', cx + 1, y0 + 11.5, 5, 6, 1, '100 V power FET'],
          ['ic', cx - 6.5, y0 + 19, 6, 5, 0.9, 'BQ25756 buck-boost'], ['res', cx + 0.8, y0 + 18.5, 6.3, 3.2, 0.6, '5 mOhm 2512 sense'], ['res', cx + 0.8, y0 + 22.4, 6.3, 3.2, 0.6, '5 mOhm 2512 sense'],
          ['mlcc', cx - 7, y0 + 25, 3.2, 1.6, 1.4, 'MLCC 1206'], ['mlcc', cx - 3.4, y0 + 25, 3.2, 1.6, 1.4, 'MLCC 1206']];
        for (const [k, x, y, w, d, h, lab] of S) if (!hit(x, y, w, d, h)) put(k, x, y, w, d, h, `${lab} (port ${i + 1})`, z); else place(k, w, d, h, `${lab} (port ${i + 1})`, zs);
      }
    } else for (const kk of kits) for (const [k, w, d, h, n, lab] of KIT[kk]) for (let i = 0; i < n; i++) if (!place(k, w, d, h, lab, zs)) break;
  }
  return { parts, miss };
}

/* ------------------------------------------------------------------ viewer */
const TOK = { bg: ['--model-bg', '#e9eef3', '#0d1311'], copper: ['--model-copper', '#c9a44c', '#d2b05c'], mask: ['--model-mask', '#17191c', '#0b0d0c'], silk: ['--model-silk', '#f1f2ec', '#e6e8e1'], alu: ['--model-alu', '#b7bec7', '#8d959f'], cap: ['--model-cap', '#2a2e34', '#20242a'] };
let cctx;
function readTokens(el) {
  const cs = getComputedStyle(el), th = document.documentElement.getAttribute('data-theme');
  const dark = th === 'dark' || (th !== 'light' && matchMedia('(prefers-color-scheme: dark)').matches);
  cctx = cctx || document.createElement('canvas').getContext('2d');
  const T = {};
  for (const k in TOK) {
    const [name, l, dk] = TOK[k], def = dark ? dk : l, v = cs.getPropertyValue(name).trim() || def;
    cctx.fillStyle = def; cctx.fillStyle = v;
    T[k] = new THREE.Color(/^(#|rgb)/.test(cctx.fillStyle) ? cctx.fillStyle.replace(/rgba\(([^,]+,[^,]+,[^,]+),[^)]+\)/, 'rgb($1)') : def);
  }
  return T;
}

const CSS = `.d3v{position:relative;width:100%;height:100%;min-height:320px;overflow:hidden;border-radius:inherit;background:var(--model-bg,#e9eef3);color:inherit;font:13px/1.35 system-ui,-apple-system,"Segoe UI",sans-serif;-webkit-user-select:none;user-select:none}
.d3v canvas{position:absolute;inset:0;display:block;width:100%;height:100%;touch-action:none;outline:none}
.d3v-hint{position:absolute;top:10px;left:12px;right:12px;font-size:12px;opacity:.72;pointer-events:none;transition:opacity .2s}
.d3v-bar{position:absolute;left:10px;right:10px;bottom:10px;display:flex;flex-wrap:wrap;gap:6px;pointer-events:none}
.d3v-bar button{pointer-events:auto;font:inherit;font-weight:600;padding:7px 12px;border-radius:999px;border:1px solid color-mix(in srgb,currentColor 22%,transparent);background:color-mix(in srgb,var(--model-bg,#e9eef3) 82%,transparent);color:inherit;cursor:pointer;-webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px)}
.d3v-bar button[aria-pressed=true]{background:var(--model-copper,#c9a44c);border-color:transparent;color:#15130d}
.d3v-bar .d3v-ports{margin-left:auto}
.d3v button:focus-visible{outline:2px solid var(--model-copper,#c9a44c);outline-offset:2px}
.d3v-tip{position:absolute;left:0;top:0;pointer-events:none;max-width:250px;padding:6px 9px;border-radius:6px;background:rgba(12,14,16,.93);color:#f3f4f1;font-size:12px;box-shadow:0 4px 14px rgba(0,0,0,.25);opacity:0;transition:opacity .12s}
.d3v-tip b{font-family:ui-monospace,Consolas,monospace;color:#e8c36a;margin-right:6px}.d3v-tip small{display:block;opacity:.72;margin-top:2px}
.d3v-list{position:absolute;right:10px;bottom:54px;max-height:calc(100% - 100px);overflow:auto;padding:6px;border-radius:10px;background:color-mix(in srgb,var(--model-bg,#e9eef3) 94%,transparent);border:1px solid color-mix(in srgb,currentColor 18%,transparent)}
.d3v-list button{display:block;width:100%;text-align:left;font:12px ui-monospace,Consolas,monospace;background:none;border:0;color:inherit;padding:4px 8px;border-radius:6px;cursor:pointer}
.d3v-list button:hover{background:color-mix(in srgb,currentColor 10%,transparent)}
.d3v-note{font-size:.9em;opacity:.8}
@media (prefers-reduced-motion:reduce){.d3v-tip,.d3v-hint{transition:none}}`;

function rrect(x, y, w, h, r) {
  const s = new THREE.Shape(); r = Math.max(0.01, Math.min(r, w / 2, h / 2));
  s.moveTo(x + r, y); s.lineTo(x + w - r, y); s.absarc(x + w - r, y + r, r, -Math.PI / 2, 0);
  s.lineTo(x + w, y + h - r); s.absarc(x + w - r, y + h - r, r, 0, Math.PI / 2);
  s.lineTo(x + r, y + h); s.absarc(x + r, y + h - r, r, Math.PI / 2, Math.PI);
  s.lineTo(x, y + r); s.absarc(x + r, y + r, r, Math.PI, 1.5 * Math.PI); return s;
}
const circ = (x, y, r) => new THREE.Path().absarc(x, y, r, 0, Math.PI * 2, true);
function canvasTex(w, h, draw, srgb) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); if (srgb) t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
}

function start(host, S) {
  const L = layout(S), out = L.out;
  const cx = (out.x0 + out.x1) / 2, cy = (out.y0 + out.y1) / 2, cz = (out.z0 + out.z1) / 2;
  const mqReduce = matchMedia('(prefers-reduced-motion: reduce)');
  let reduced = mqReduce.matches;

  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap; renderer.shadowMap.autoUpdate = false;

  // ---- DOM
  if (!document.getElementById('d3v-css')) { const st = document.createElement('style'); st.id = 'd3v-css'; st.textContent = CSS; document.head.appendChild(st); }
  const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt) e.textContent = txt; return e; };
  const wrap = el('div', 'd3v'); wrap.setAttribute('role', 'region'); wrap.setAttribute('aria-label', 'Interactive 3D model of the Battery Bank');
  const canvas = renderer.domElement; canvas.setAttribute('role', 'img');
  canvas.setAttribute('aria-label', `3D model: ${S.enclosure.outer.length} x ${S.enclosure.outer.width} x ${S.enclosure.outer.height} mm aluminium enclosure with two stacked PCBs and a swappable battery cartridge`);
  const touch = matchMedia('(pointer: coarse)').matches, wheelAlways = host.dataset.wheel === 'always';
  const hintTxt = touch ? 'Drag to orbit \u00b7 pinch to zoom \u00b7 two fingers to pan \u00b7 tap a port' : `Drag to orbit \u00b7 right-drag to pan \u00b7 ${wheelAlways ? 'scroll' : 'click, then scroll'} to zoom \u00b7 hover a port`;
  const hint = el('div', 'd3v-hint', hintTxt), tip = el('div', 'd3v-tip'), bar = el('div', 'd3v-bar');
  bar.setAttribute('role', 'toolbar'); bar.setAttribute('aria-label', 'Model views');
  const list = el('div', 'd3v-list'); list.id = 'd3v-list-' + Math.random().toString(36).slice(2, 7); list.hidden = true;
  wrap.append(canvas, hint, tip, list, bar);
  host.replaceChildren(wrap);
  if (wrap.clientHeight < 330) wrap.style.aspectRatio = '16 / 10'; // host has no height of its own

  // ---- scene
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(32, 1.6, 2, 5000);
  const root = new THREE.Group(); root.rotation.x = -Math.PI / 2; scene.add(root); // spec +Z -> world up, spec +Y -> away from camera
  const model = new THREE.Group(); model.position.set(-cx, -cy, -cz); root.add(model);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x3b4250, 0.75));
  const key = new THREE.DirectionalLight(0xffffff, 2.4); key.position.set(160, 300, 200); key.castShadow = true;
  Object.assign(key.shadow.camera, { left: -260, right: 260, top: 260, bottom: -260, near: 10, far: 1000 });
  key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -0.0004; key.shadow.normalBias = 0.4; scene.add(key);
  const fill = new THREE.DirectionalLight(0xdfe8ff, 0.7); fill.position.set(-220, 120, -160); scene.add(fill);
  { // procedural studio environment for reflections
    const env = new THREE.Scene(), bm = (c) => new THREE.MeshBasicMaterial({ color: c, side: THREE.BackSide });
    env.add(new THREE.Mesh(new THREE.BoxGeometry(10, 10, 10), bm(0x8a9199)));
    const panel = (p, sx, sy, i) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(sx, sy), new THREE.MeshBasicMaterial({ color: new THREE.Color(i, i, i), side: THREE.DoubleSide })); m.position.set(...p); m.lookAt(0, 0, 0); env.add(m); };
    panel([0, 4.8, 0], 7, 7, 4); panel([4.8, 1, 2], 3, 6, 3); panel([-4.8, 0.5, -1], 3, 5, 1.8); panel([0, 1, -4.8], 8, 2.5, 2.2); panel([0, 0.5, 4.8], 6, 2, 1.6);
    const pm = new THREE.PMREMGenerator(renderer); scene.environment = pm.fromScene(env, 0.03).texture; pm.dispose();
  }
  const groundY = out.z0 - cz;
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(2000, 2000), new THREE.ShadowMaterial({ opacity: 0.22 }));
  ground.rotation.x = -Math.PI / 2; ground.position.y = groundY; ground.receiveShadow = true; scene.add(ground);
  const blob = new THREE.Mesh(new THREE.PlaneGeometry((out.x1 - out.x0) * 1.7, (out.y1 - out.y0) * 1.9), new THREE.MeshBasicMaterial({ color: 0, transparent: true, depthWrite: false, opacity: 0.38,
    alphaMap: canvasTex(128, 128, (g) => { const gr = g.createRadialGradient(64, 64, 4, 64, 64, 64); gr.addColorStop(0, '#fff'); gr.addColorStop(1, '#000'); g.fillStyle = gr; g.fillRect(0, 0, 128, 128); }) }));
  blob.rotation.x = -Math.PI / 2; blob.position.y = groundY + 0.05; scene.add(blob);

  // ---- materials
  const std = (o) => new THREE.MeshStandardMaterial(o), phy = (o) => new THREE.MeshPhysicalMaterial(o);
  const brushed = canvasTex(512, 4, (g, w, h) => { for (let x = 0; x < w; x++) { const v = 150 + (Math.random() - 0.5) * 80; g.fillStyle = `rgb(${v},${v},${v})`; g.fillRect(x, 0, 1, h); } });
  brushed.wrapS = brushed.wrapT = THREE.RepeatWrapping; brushed.repeat.set(1 / 45, 1 / 45);
  const M = {
    alu: phy({ metalness: 1, roughness: 0.62, roughnessMap: brushed, anisotropy: 0.55, anisotropyRotation: Math.PI / 2, transparent: true }),
    cap: phy({ roughness: 0.55, clearcoat: 0.25, clearcoatRoughness: 0.5, transparent: true }),
    capPC: phy({ roughness: 0.22, clearcoat: 0.7, transparent: true, opacity: 0.8 }),
    glass: phy({ color: 0x07090c, roughness: 0.05, metalness: 0.1, clearcoat: 1, transparent: true, opacity: 0.9 }),
    cartShell: phy({ color: 0x2c3138, roughness: 0.45, clearcoat: 0.3, transparent: true }),
    fr4: std({ color: 0x8d7c4e, roughness: 0.85 }), gold: std({ metalness: 1, roughness: 0.26 }), silk: std({ roughness: 0.9 }),
    ic: std({ color: 0x18191b, roughness: 0.42 }), ind: std({ color: 0x35373b, roughness: 0.72 }), mlcc: std({ color: 0xb59b72, roughness: 0.6 }),
    can: std({ color: 0xc6cad0, metalness: 1, roughness: 0.32 }), nickel: std({ color: 0xd0d4d9, metalness: 1, roughness: 0.3 }),
    plastic: std({ color: 0x1b1c1f, roughness: 0.55 }), dark: std({ color: 0x050506, roughness: 0.9 }), modpcb: std({ color: 0x1c2a44, roughness: 0.6 }),
    brass: std({ color: 0xc19a45, metalness: 1, roughness: 0.35 }), white: std({ color: 0xf4f4f0, roughness: 0.5 }),
    cell: phy({ color: 0x2d4f86, roughness: 0.32, clearcoat: 0.6 }), xt60: std({ color: 0xe8c21c, roughness: 0.5 }), ferrite: std({ color: 0x2b2b2d, roughness: 0.8 }),
    glow: std({ color: 0x0b1416, emissive: 0x2fc8f0, emissiveIntensity: 1.2, roughness: 0.3, transparent: true, opacity: 0.95 }),
    pipe: std({ color: 0xf2f6f8, emissive: 0x9fdcff, emissiveIntensity: 0.25, roughness: 0.3 }),
    ledG: std({ color: 0x0a2a0a, emissive: 0x2cff5a, emissiveIntensity: 1.4 }), ledA: std({ color: 0x2a1a05, emissive: 0xffa31a, emissiveIntensity: 1.2 }),
    slot: std({ color: 0x050506, roughness: 0.9, transparent: true }),
    lens: phy({ color: 0xeaf2f8, roughness: 0.04, clearcoat: 1, transparent: true, opacity: 0.45 }),
  };
  M.masks = [];
  const shell = [[M.alu, 1, 0.07], [M.cap, 1, 0.09], [M.capPC, 0.8, 0.08], [M.glass, 0.9, 0.12], [M.cartShell, 1, 0.22], [M.slot, 1, 0.1]];
  function applyTheme() {
    const T = readTokens(host);
    scene.background = T.bg; M.alu.color.copy(T.alu); M.cap.color.copy(T.cap); M.capPC.color.copy(T.cap).lerp(new THREE.Color(0xffffff), 0.25);
    M.gold.color.copy(T.copper); M.silk.color.copy(T.silk); for (const m of M.masks) m.color.copy(T.mask);
    for (const m of M.decoGold || []) m.color.copy(T.copper); for (const m of M.decoSilk || []) m.color.copy(T.silk);
    const lum = T.bg.r * 0.2126 + T.bg.g * 0.7152 + T.bg.b * 0.0722;
    ground.material.opacity = lum > 0.25 ? 0.2 : 0.5; blob.material.opacity = lum > 0.25 ? 0.32 : 0.6;
    if (hl) hl.material.color.copy(T.copper);
    req();
  }

  // ---- geometry helpers (all in spec coordinates inside `model`)
  const MX = new THREE.Matrix4().set(0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1); // shape (y,z), extrude -> +X
  const extrudeX = (shape, x0, len, o = {}) => { const g = new THREE.ExtrudeGeometry(shape, { depth: len, bevelEnabled: false, curveSegments: 12, ...o }); g.applyMatrix4(MX); g.translate(x0, 0, 0); return g; };
  const mesh = (geo, mat, parent, cast = true, recv = true) => { const m = new THREE.Mesh(geo, mat); m.castShadow = cast; m.receiveShadow = recv; parent.add(m); return m; };
  const boxAt = (parent, mat, x0, y0, z0, w, d, h) => { const m = mesh(new THREE.BoxGeometry(w, d, h), mat, parent); m.position.set(x0 + w / 2, y0 + d / 2, z0 + h / 2); return m; };
  const cylZ = (parent, mat, x, y, z0, r, h, seg = 32) => { const m = mesh(new THREE.CylinderGeometry(r, r, h, seg), mat, parent); m.rotation.x = Math.PI / 2; m.position.set(x, y, z0 + h / 2); return m; };
  const grp = (parent = model) => { const g = new THREE.Group(); parent.add(g); return g; };
  const G = { body: grp(), capL: grp(), capR: grp(), cart: grp(), led: grp(), spk: grp(), coil: grp(), hdr: grp(), fan: grp(), boards: {}, lift: {} };
  const pick = [], occluders = [], portItems = [];
  const info = (o, i) => { o.userData.info = i; pick.push(o); return o; };

  // ---- enclosure
  const prof = (inset) => rrect(out.y0 + inset, out.z0 + inset, out.y1 - out.y0 - 2 * inset, out.z1 - out.z0 - 2 * inset, L.r - inset);
  const bodyShape = prof(0); bodyShape.holes.push(prof(L.w));
  const bodyMesh = mesh(extrudeX(bodyShape, L.body.x0, L.body.x1 - L.body.x0, { curveSegments: 16 }), M.alu, G.body);
  occluders.push(bodyMesh);
  const bv = 1.2, capGeo = (x0) => extrudeX(prof(bv), x0 + bv, L.capR.x1 - L.capR.x0 - 2 * bv, { bevelEnabled: true, bevelSize: bv, bevelThickness: bv, bevelSegments: 3, curveSegments: 16 });
  const capLMesh = mesh(capGeo(L.capL.x0), M.capPC, G.capL), capRMesh = mesh(capGeo(L.capR.x0), M.cap, G.capR);
  occluders.push(capLMesh, capRMesh);
  // top window (corner radius assumed 3)
  const win = mesh(new THREE.ExtrudeGeometry(rrect(L.win.cx - L.win.sx / 2, L.win.cy - L.win.sy / 2, L.win.sx, L.win.sy, 3), { depth: 0.6, bevelEnabled: false }), M.glass, G.body, false);
  win.position.z = out.z1 - 0.45; occluders.push(win);
  const ring = mesh(new THREE.RingGeometry(17.4, 18, 64), M.silk, G.body, false); ring.position.set(L.win.cx, L.win.cy, out.z1 + 0.17);
  // perforations: instanced dark discs
  const holes = (pts, r, normal) => {
    const geo = new THREE.CircleGeometry(r, 12), im = new THREE.InstancedMesh(geo, M.dark, pts.length), m4 = new THREE.Matrix4(), q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), normal);
    pts.forEach((p, i) => im.setMatrixAt(i, m4.compose(p, q, new THREE.Vector3(1, 1, 1)))); G.body.add(im); return im;
  };
  const hex = (r, pitch, f) => { const pts = []; for (let j = -Math.ceil(r / pitch); j <= r / pitch; j++) for (let i = -Math.ceil(r / pitch) - 1; i <= r / pitch + 1; i++) { const u = (i + (j & 1) * 0.5) * pitch, v = j * pitch * 0.866; if (u * u + v * v <= r * r) { const p = f(u, v); if (p) pts.push(p); } } return pts; };
  info(holes(hex(L.spkG.rad - 1.2, 2.3, (u, v) => new THREE.Vector3(L.spkG.cx + u, L.spkG.cy + v, out.z1 + 0.03)), 0.62, new THREE.Vector3(0, 0, 1)), { ref: 'Speaker grille', type: `top face, D${L.spkG.rad * 2} mm`, sub: `centre x ${L.spkG.cx}, y ${L.spkG.cy}` });
  const fz = L.fanG; // clipped to the flat part of the back face
  info(holes(hex(fz.s / 2 - 0.8, 2.6, (u, v) => (fz.cz + v < fz.zFlat - 0.9 && fz.cz + v > fz.zLow + 0.9 ? new THREE.Vector3(fz.cx + u, out.y1 + 0.03, fz.cz + v) : null)), 0.8, new THREE.Vector3(0, 1, 0)), { ref: 'Fan grille', type: `back face, ${fz.s} mm`, sub: `centre x ${fz.cx}, z ${fz.cz}` });
  const glow = boxAt(G.body, M.glow, L.glow.x0, out.y0 - 0.6, L.glow.z0, L.glow.x1 - L.glow.x0, 0.8, L.glow.z1 - L.glow.z0); glow.castShadow = false;
  info(glow, { ref: 'Glow light strip', type: `light pipe + ${L.glowLeds || 8}x SK6812MINI-E`, sub: `front-top edge, x ${L.glow.x0}-${L.glow.x1}` });
  for (let i = 0, n = L.glowLeds || 8; i < n; i++) boxAt(G.body, M.glow, L.glow.x0 + (L.glow.x1 - L.glow.x0) * (i + 0.5) / n - 1.6, 0.05, L.glow.z0, 3.2, 0.9, L.glow.z1 - L.glow.z0).castShadow = false;
  { const t = mesh(new THREE.RingGeometry(L.tripod.r, L.tripod.r + 2, 32), M.brass, G.body, false); t.rotation.x = Math.PI; t.position.set(L.tripod.cx, L.tripod.cy, out.z0 - 0.03);
    const h = mesh(new THREE.CircleGeometry(L.tripod.r, 24), M.dark, G.body, false); h.rotation.x = Math.PI; h.position.set(L.tripod.cx, L.tripod.cy, out.z0 - 0.02); }
  // right-cap cartridge door, hinged on its top edge (opening = cartridge cross-section)
  const ct = L.cart;
  const doorOpen = mesh(extrudeX(rrect(ct.y0, ct.z0, ct.y1 - ct.y0, ct.z1 - ct.z0, 2), out.x1 - 0.2, 0.25), M.slot, G.capR, false);
  const door = grp(G.capR); door.position.set(out.x1, 0, ct.z1);
  mesh(extrudeX(rrect(ct.y0 + 0.4, ct.z0 + 0.4 - ct.z1, ct.y1 - ct.y0 - 0.8, ct.z1 - ct.z0 - 0.8, 1.8), 0, 0.9), M.cap, door);
  boxAt(door, M.slot, 0.9, (ct.y0 + ct.y1) / 2 - 8, -4.5, 0.15, 16, 2.4); // finger notch
  info(door, { ref: 'Cartridge door', type: 'right end cap, cartridge latch', sub: 'Cartridge out opens it' });

  // ---- connectors: local frame = mouth at y=0 facing +Y, body toward -Y, centred in x/z
  function connector(c, face) {
    const g = new THREE.Group(), w = c.w, h = c.h, d = face ? 0.6 : c.d, T = c.type;
    const box = (mat, bw, bd, bh, x = 0, y = -bd / 2, z = 0) => { const m = new THREE.Mesh(new THREE.BoxGeometry(bw, bd, bh), mat); m.position.set(x, y, z); m.castShadow = !face; g.add(m); return m; };
    const prism = (shape, dep, mat) => { const geo = new THREE.ExtrudeGeometry(shape, { depth: dep, bevelEnabled: false, curveSegments: 10 }); geo.rotateX(Math.PI / 2); const m = new THREE.Mesh(geo, mat); m.castShadow = !face; g.add(m); return m; };
    const disc = (mat, r, y, x = 0, z = 0) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, 0.3, 28), mat); m.position.set(x, y, z); g.add(m); return m; };
    const shellRing = (rr, th) => { const s = rrect(-w / 2, -h / 2, w, h, rr); s.holes.push(rrect(-w / 2 + th, -h / 2 + th, w - 2 * th, h - 2 * th, Math.max(0.05, rr - th))); prism(s, d, M.nickel); box(M.dark, w - 2 * th, 0.2, h - 2 * th, 0, -Math.min(d, 2.4)); };
    if (face) box(M.dark, w + 0.8, 0.3, h + 0.8, 0, -0.2);
    if (/USB-C/i.test(T)) { shellRing(h / 2, 0.42); box(M.plastic, w * 0.62, Math.min(d, 2.4), 0.7, 0, -Math.min(d, 2.4) / 2 - 0.05); }
    else if (/USB-A/i.test(T)) { shellRing(0.5, 0.35); box(M.plastic, w - 2.6, Math.min(d, 5), h * 0.34, 0, -Math.min(d, 5) / 2 - 0.1, h * 0.14); for (let i = 0; i < 4; i++) box(M.gold, 1, 0.4, 0.1, -3.6 + i * 2.4, -0.4, h * 0.14 - h * 0.17); }
    else if (/barrel/i.test(T)) { if (!face) box(M.plastic, w, d, h, 0, -d / 2); disc(M.dark, Math.min(w, h) * 0.33, 0.06); const pin = num(T, /([\d.]+)\s*mm/, 2) / 2; const p = disc(M.nickel, pin * 0.55, 0.1); p.scale.y = 2; }
    else if (/RJ45/i.test(T)) { if (!face) box(M.nickel, w, d, h, 0, -d / 2); box(M.dark, w - 3, 0.25, h * 0.6, 0, 0.02, h * 0.06); box(M.dark, w * 0.36, 0.25, h * 0.2, 0, 0.02, -h * 0.3); box(M.ledG, 2.2, 0.3, 1.4, -w / 2 + 2, 0.06, -h / 2 + 1.3); box(M.ledA, 2.2, 0.3, 1.4, w / 2 - 2, 0.06, -h / 2 + 1.3); }
    else if (/slide/i.test(T)) { if (!face) box(M.nickel, w, d, h, 0, -d / 2); box(M.dark, w * 0.72, 0.25, Math.min(2.2, h * 0.7), 0, 0.02); box(M.plastic, 2.6, 1.4, 1.6, -w * 0.16, 0.5); }
    else if (/tactile/i.test(T)) { if (!face) box(M.plastic, w, d, h, 0, -d / 2); disc(M.dark, w * 0.42, 0.04); const rec = /recess/i.test(T), b = new THREE.Mesh(new THREE.CylinderGeometry(rec ? 0.9 : 1.55, rec ? 0.9 : 1.55, rec ? 0.6 : 1.4, 24), /light-pipe/i.test(T) ? M.pipe : M.plastic); b.position.y = rec ? -0.2 : 0.5; g.add(b); }
    else if (/microSD/i.test(T)) { if (!face) box(M.nickel, w, d, h, 0, -d / 2); box(M.dark, w - 2, 0.25, h * 0.6, 0, 0.02); }
    else box(M.plastic, w, d, h, 0, -d / 2);
    return g;
  }

  // ---- boards
  let hl; const hlBox = new THREE.Box3();
  for (const b of L.boards) {
    const og = grp(), bg = grp(og); bg.position.set(b.p.x, b.p.y, b.p.z); G.boards[b.id] = bg; G.lift[b.id] = og; // og = explode offset
    const { parts } = populate(L, b);
    const s = 6, cw = Math.ceil(b.W * s), ch = Math.ceil(b.H * s), Y = (y) => (b.H - y) * s;
    const R = (g, x, y, w, d) => g.fillRect(x * s, Y(y + d), w * s, d * s), C = (g, x, y, r) => { g.beginPath(); g.arc(x * s, Y(y), r * s, 0, 7); g.fill(); };
    const maskTex = canvasTex(cw, ch, (g) => { // traces / pours under the mask (lighter = copper)
      g.fillStyle = '#c4c4c4'; g.fillRect(0, 0, cw, ch); g.fillStyle = '#d2d2d2';
      for (const z of b.zones || []) R(g, z.x0 + 0.6, z.y0 + 0.6, z.x1 - z.x0 - 1.2, z.y1 - z.y0 - 1.2);
      g.strokeStyle = '#ececec'; g.lineCap = 'round';
      parts.forEach((p, i) => { const q = parts[i + 1]; if (!q || q.zone !== p.zone) return; g.lineWidth = (p.k === 'ind' || q.k === 'ind' ? 1.4 : 0.3) * s; g.beginPath(); g.moveTo((p.x + p.w / 2) * s, Y(p.y + p.d / 2)); g.lineTo((q.x + q.w / 2) * s, Y(p.y + p.d / 2)); g.lineTo((q.x + q.w / 2) * s, Y(q.y + q.d / 2)); g.stroke(); });
    }, true);
    maskTex.repeat.set(1 / b.W, 1 / b.H);
    const maskMat = std({ roughness: 0.72, map: maskTex, envMapIntensity: 0.55 }); M.masks.push(maskMat);
    const shape = rrect(0, 0, b.W, b.H, b.outline.corner_radius);
    for (const h of b.mounting_holes || []) shape.holes.push(circ(h.x, h.y, h.d / 2));
    const boardMesh = mesh(new THREE.ExtrudeGeometry(shape, { depth: b.t, bevelEnabled: false, curveSegments: 16 }), [maskMat, M.fr4], bg);
    info(boardMesh, { ref: b.name, type: `${b.W} x ${b.H} mm, ${b.layers}-layer, ${b.finish}, ${b.mask} mask`, sub: `z ${b.p.z} mm \u00b7 ${b.assembly || ''}` });
    const copper = canvasTex(cw, ch, (g) => {
      g.fillStyle = '#000'; g.fillRect(0, 0, cw, ch); g.fillStyle = '#fff';
      for (const h of b.mounting_holes || []) C(g, h.x, h.y, h.d / 2 + 1.4);
      for (const q of L.bosses) if (q.board === b.id) C(g, q.x, q.y, 2.6);
      for (const f of [[2, 12], [b.W - 2, 12], [2, b.H - 12]]) C(g, f[0], f[1], 0.5);
      for (const p of parts) {
        if (p.k === 'ic') R(g, p.x - 0.35, p.y - 0.35, p.w + 0.7, p.d + 0.7);
        else if (p.k === 'ind' || p.k === 'xfmr') { R(g, p.x - 0.5, p.y + p.d * 0.15, p.w * 0.3, p.d * 0.7); R(g, p.x + p.w * 0.7 + 0.5, p.y + p.d * 0.15, p.w * 0.3, p.d * 0.7); }
        else if (p.k === 'mlcc' || p.k === 'res') { R(g, p.x - 0.3, p.y - 0.15, p.w * 0.36, p.d + 0.3); R(g, p.x + p.w * 0.64 + 0.3, p.y - 0.15, p.w * 0.36, p.d + 0.3); }
        else if (p.k === 'can') C(g, p.x + p.w / 2, p.y + p.d / 2, p.w / 2 + 0.4);
        else if (p.k === 'mod') for (let t = 0.8; t < p.d - 0.4; t += 1.27) { R(g, p.x - 0.6, p.y + t, 1.2, 0.8); R(g, p.x + p.w - 0.6, p.y + t, 1.2, 0.8); }
        else R(g, p.x - 0.3, p.y - 0.3, p.w + 0.6, p.d + 0.6);
      }
      for (const h of L.hdrs) if (h.upper === b.id) { // pin pads of each B2B part on the upper board
        if (h.mezz) for (let x = h.lx0 + 0.6; x < h.lx0 + h.lw - 0.4; x += 0.8) { R(g, x, h.ly0 + 0.3, 0.4, 1.2); R(g, x, h.ly0 + h.ld - 1.5, 0.4, 1.2); }
        else for (let i = 0; i < h.cols; i++) for (let j = 0; j < h.rows; j++) C(g, h.lx0 + (h.lw - h.cols * h.pitch) / 2 + (i + 0.5) * h.pitch, h.ly0 + (h.ld - h.rows * h.pitch) / 2 + (j + 0.5) * h.pitch, h.pitch * 0.3);
      }
    });
    const silk = canvasTex(cw, ch, (g) => {
      g.fillStyle = '#000'; g.fillRect(0, 0, cw, ch); g.fillStyle = g.strokeStyle = '#fff'; g.lineWidth = 0.15 * s;
      g.font = `600 ${1.25 * s}px ui-monospace,Consolas,monospace`; g.textBaseline = 'top';
      for (const z of b.zones || []) { g.setLineDash([0.8 * s, 0.6 * s]); g.strokeRect(z.x0 * s + 2, Y(z.y1) + 2, (z.x1 - z.x0) * s - 4, (z.y1 - z.y0) * s - 4); g.setLineDash([]); }
      for (const h of b.mounting_holes || []) { g.beginPath(); g.arc(h.x * s, Y(h.y), (h.d / 2 + 2) * s, 0, 7); g.stroke(); }
      for (const c of b.conns) { const ty = c.side ? c.y + 0.6 : c.front ? c.fy0 + c.fd + 2.1 : c.fy0 - 0.6; g.textAlign = c.side ? 'left' : 'center'; g.fillText(c.ref.replace(/^J_|^SW_/, ''), (c.side ? c.fx0 + c.fw + 1 : c.x) * s, Y(ty)); }
      g.setLineDash([1.6 * s, 0.5 * s, 0.3 * s, 0.5 * s]); for (const q of b.ko) g.strokeRect(q.x0 * s + 5, Y(q.y1) + 5, (q.x1 - q.x0) * s - 10, (q.y1 - q.y0) * s - 10); g.setLineDash([]);
      for (const q of b.ko) g.fillText(`MAX ${q.max_height} MM`, q.x0 * s + 9, Y(q.y0) - 1.8 * s);
      for (const q of L.bosses) if (q.board === b.id) { g.beginPath(); g.arc(q.x * s, Y(q.y), 3.2 * s, 0, 7); g.stroke(); }
      g.textAlign = 'left';
      for (const p of parts) { if (p.k === 'ic' && p.w >= 3) C(g, p.x - 0.7, p.y + p.d + 0.7, 0.3); if (p.k === 'ind') g.strokeRect(p.x * s - 3, Y(p.y + p.d) - 3, p.w * s + 6, p.d * s + 6); }
      // title in the first free horizontal gap between zones on the left half
      const iv = (b.zones || []).filter((z) => z.x0 < b.W / 2).map((z) => [z.y0, z.y1]).sort((p, q) => p[0] - q[0]);
      let gy = null, end = -1; for (const [y0, y1] of iv) { if (end >= 0 && y0 - end >= 1.6) { gy = end; break; } end = Math.max(end, y1); }
      g.font = `700 ${1.2 * s}px ui-monospace,Consolas,monospace`;
      if (gy !== null) g.fillText(`${b.name.toUpperCase()} \u00b7 REV ${S.rev} \u00b7 ${b.layers}L ${b.finish} \u00b7 OPEN HARDWARE`, 4.5 * s, Y(gy + 1.55));
    });
    const deco = (tex, mat, z) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(b.W, b.H), mat.clone()); m.material.alphaMap = tex; m.material.alphaTest = 0.5; m.material.polygonOffset = true; m.material.polygonOffsetFactor = -2; m.position.set(b.W / 2, b.H / 2, b.t + z); m.receiveShadow = true; bg.add(m); return m.material; };
    const gm = deco(copper, M.gold, 0.02), sm = deco(silk, M.silk, 0.03);
    M.decoGold = (M.decoGold || []).concat(gm); M.decoSilk = (M.decoSilk || []).concat(sm);
    // instanced components
    const unitBox = new THREE.BoxGeometry(1, 1, 1).translate(0.5, 0.5, 0.5), unitCyl = new THREE.CylinderGeometry(0.5, 0.5, 1, 20).rotateX(Math.PI / 2).translate(0.5, 0.5, 0.5);
    const kinds = { ic: M.ic, res: M.ic, ind: M.ind, xfmr: M.ind, mlcc: M.mlcc, can: M.can, conn: M.nickel, modpcb: M.modpcb, shield: M.nickel };
    const inst = {};
    const addI = (k, p, x, y, z, w, d, h) => (inst[k] = inst[k] || []).push({ p, x, y, z, w, d, h });
    for (const p of parts) {
      if (p.k === 'mod') { addI('modpcb', p, p.x, p.y, 0, p.w, p.d, 0.8); addI('shield', p, p.x + 1, p.y + 1, 0.8, p.w - 2, p.d - Math.min(6, p.d * 0.25), p.h - 0.8); }
      else addI(p.k, p, p.x, p.y, 0, p.w, p.d, p.h);
    }
    const m4 = new THREE.Matrix4(), q0 = new THREE.Quaternion(), v1 = new THREE.Vector3(), v2 = new THREE.Vector3();
    for (const k in inst) {
      const arr = inst[k], im = new THREE.InstancedMesh(k === 'can' ? unitCyl : unitBox, kinds[k], arr.length);
      arr.forEach((a, i) => im.setMatrixAt(i, m4.compose(v1.set(a.x, a.y, b.t + a.z), q0, v2.set(a.w, a.d, a.h))));
      im.castShadow = im.receiveShadow = true; im.userData.parts = arr.map((a) => a.p); im.userData.board = b.name; bg.add(im); pick.push(im);
    }
    for (const q of L.bosses) if (q.board === b.id) cylZ(bg, M.nickel, q.x, q.y, b.t, 2.7, 1.5, 24);
    // edge connectors on the board + matching openings in the wall
    for (const c of b.conns) {
      const ci = { ref: c.ref, type: c.type, sub: `${b.name} \u00b7 ${c.edge} edge \u00b7 ${c.side ? 'y ' + c.y : 'x ' + c.x} mm \u00b7 ${c.w} x ${c.h} mm` };
      const cg = connector(c, false); cg.position.set(c.mx, c.my, c.zc); cg.rotation.z = c.rot; bg.add(cg); info(cg, ci);
      if (!c.side) { const fg = connector(c, true); fg.position.set(b.p.x + c.x, c.front ? out.y0 - 0.02 : out.y1 + 0.02, b.p.z + c.zc); fg.rotation.z = c.rot; G.body.add(fg); info(fg, ci); }
      portItems.push({ label: `${c.ref}  ${c.type}`, obj: cg, info: ci });
    }
  }
  // B2B header + standoffs between stacked boards
  for (const h of L.hdrs) {
    const hg = boxAt(G.hdr, h.mezz ? M.ind : M.plastic, h.wx + h.lx0, h.wy + h.ly0, h.z0, h.lw, h.ld, h.z1 - h.z0);
    const ii = { ref: `B2B ${h.name || 'header'}`, type: h.type, sub: `x ${h.x}, y ${h.y} \u00b7 ${(h.z1 - h.z0).toFixed(1)} mm stack \u00b7 ${h.orientation || 'along X'}` };
    info(hg, ii); portItems.push({ label: `B2B  ${h.name || h.type}`, obj: hg, info: ii });
  }
  // card-guide rails in the extrusion (notched at edge connectors) + end-cap screw bosses
  for (const b of L.boards) if (b.rails) {
    const e = b.rails + Math.min(b.p.y, L.inn.y - b.p.y - b.H), x0 = L.body.x0, x1 = L.body.x1;
    for (const front of [true, false]) {
      const cuts = b.conns.filter((c) => !c.side && c.front === front).map((c) => [b.p.x + c.x - c.w / 2 - 1, b.p.x + c.x + c.w / 2 + 1]).sort((p, q) => p[0] - q[0]);
      const segs = []; let a = x0; for (const [c0, c1] of cuts) { if (c0 > a) segs.push([a, c0]); a = Math.max(a, c1); } if (a < x1) segs.push([a, x1]);
      for (const [s0, s1] of segs) for (const z of [b.p.z - 1.2, b.top + 0.05]) boxAt(G.body, M.alu, s0, front ? 0 : L.inn.y - e, z, s1 - s0, e, 1.15);
    }
  }
  for (const q of L.bosses) {
    const b = L.boards.find((k) => k.id === q.board), wx = b.p.x + q.x, left = wx < (L.out.x0 + L.out.x1) / 2;
    const xa = left ? 0 : wx - 3.5, xb = left ? wx + 3.5 : L.inn.x; // boss runs from the end-cap wall to the screw
    const m = boxAt(left ? G.capL : G.capR, M.cap, xa, b.p.y + q.y - 3.5, b.p.z - 4, xb - xa, 7, 4);
    info(m, { ref: 'Screw boss', type: `end-cap boss under ${b.name}`, sub: `board-local x ${q.x}, y ${q.y} (boss size assumed)` });
  }
  for (const up of L.boards) for (const lo of L.boards) {
    const gap = up.p.z - lo.top; if (up === lo || gap <= 0 || gap > 40) continue;
    for (const h of up.mounting_holes || []) {
      const wx = up.p.x + h.x, wy = up.p.y + h.y;
      if (!(lo.mounting_holes || []).some((k) => Math.abs(lo.p.x + k.x - wx) < 0.2 && Math.abs(lo.p.y + k.y - wy) < 0.2)) continue;
      cylZ(G.boards[lo.id], M.brass, h.x + up.p.x - lo.p.x, h.y + up.p.y - lo.p.y, lo.t, 2.75, gap, 6);
      cylZ(G.boards[up.id], M.nickel, h.x, h.y, up.t, 2.7, 1.5, 24);
    }
  }
  // LED board (vertical, faces -X) + flashlight optic in the left cap
  if (L.led) {
    const e = L.led, lg = G.led, ecy = (e.y0 + e.y1) / 2, ecz = (e.z0 + e.z1) / 2;
    info(mesh(extrudeX(rrect(e.y0, e.z0, e.W, e.H, e.outline.corner_radius), e.x0, e.t, { curveSegments: 24 }), [M.white, M.alu], lg), { ref: e.name, type: (e.parts || []).join(' + '), sub: `${e.W} x ${e.H} mm, ${e.finish}, ${e.orientation}` });
    boxAt(lg, M.white, e.x0 - 0.8, ecy - 1.5, ecz - 1.5, 0.8, 3, 3);
    const dome = mesh(new THREE.SphereGeometry(1.25, 20, 10, 0, Math.PI * 2, 0, Math.PI / 2), M.lens, lg, false); dome.rotation.z = Math.PI / 2; dome.position.set(e.x0 - 0.8, ecy, ecz);
    boxAt(lg, M.ledA, e.x0 - 0.5, ecy + 6, ecz - 0.4, 0.5, 1.6, 0.8).material = std({ color: 0x300, emissive: 0xff2010, emissiveIntensity: 0.9 });
    const lct = ((S.enclosure.end_caps || {}).left || {}).contains || [], od = num(lct.join(' '), /optic\s*D(\d+)/i, num(lct.join(' '), /(\d+)\s*mm[^,]*optic/i, 20));
    const lens = mesh(new THREE.CylinderGeometry(od / 2, od / 2, 1.2, 40), M.lens, G.capL, false); lens.rotation.z = Math.PI / 2; lens.position.set(out.x0 - 0.3, ecy, ecz);
    const bez = mesh(new THREE.TorusGeometry(od / 2 + 0.4, 0.55, 10, 48), M.nickel, G.capL, false); bez.rotation.y = Math.PI / 2; bez.position.set(out.x0 - 0.2, ecy, ecz);
    info(lens, { ref: 'Flashlight optic', type: `${od} mm optic, XP-G3 5700 K + red night LED`, sub: 'left end cap (RF window)' });
  }
  // cartridge + 5 cells
  {
    const c = L.cart, g = G.cart;
    const sh = mesh(new THREE.ExtrudeGeometry(rrect(c.x0 + 0.8, c.y0 + 0.8, c.x1 - c.x0 - 1.6, c.y1 - c.y0 - 1.6, 3), { depth: c.z1 - c.z0 - 1.6, bevelEnabled: true, bevelSize: 0.8, bevelThickness: 0.8, bevelSegments: 2 }), M.cartShell, g);
    sh.position.z = c.z0 + 0.8;
    const lab = canvasTex(512, 256, (x) => { x.fillStyle = '#000'; x.fillRect(0, 0, 512, 256); x.fillStyle = '#fff'; x.font = '700 64px system-ui,sans-serif'; x.fillText(`${c.C.energy_wh} Wh`, 28, 92); x.font = '500 30px ui-monospace,Consolas,monospace'; x.fillText((c.C.cells || '').split(' (')[0], 28, 150); x.fillText('SWAP FROM THE RIGHT  \u2192', 28, 200); });
    const lm = mesh(new THREE.PlaneGeometry(60, 30), std({ color: 0xffffff, alphaMap: lab, transparent: true, roughness: 0.6, depthWrite: false }), g, false);
    lm.position.set(c.x0 + 40, (c.y0 + c.y1) / 2, c.z1 + 0.06); M.cartLabel = lm.material;
    boxAt(g, M.plastic, c.x1, (c.y0 + c.y1) / 2 - 12, c.z1 - 7, 2, 24, 5); // pull tab
    info(sh, { ref: 'Battery cartridge', type: `${c.C.cells}`, sub: `${c.C.energy_wh} Wh \u00b7 ${c.x1 - c.x0} x ${c.y1 - c.y0} x ${c.z1 - c.z0} mm \u00b7 inserts from the ${c.C.inserts_from}` });
    for (const cell of c.cells) {
      const cy1 = new THREE.CylinderGeometry(cell.r, cell.r, cell.len - 0.8, 36), m = mesh(cy1, M.cell, g); m.position.set(cell.cx, cell.cy, cell.cz);
      if (cell.axis === 'x') m.rotation.z = Math.PI / 2;
      for (const sgn of [-1, 1]) { const e = mesh(new THREE.CylinderGeometry(cell.r * 0.86, cell.r * 0.86, 0.4, 30), M.nickel, g); e.position.copy(m.position); if (cell.axis === 'x') { e.rotation.z = Math.PI / 2; e.position.x += sgn * (cell.len / 2 - 0.2); } else e.position.y += sgn * (cell.len / 2 - 0.2); }
      info(m, { ref: '21700 cell', type: c.C.cells, sub: `centre x ${cell.cx.toFixed(1)}, y ${cell.cy.toFixed(1)}` });
    }
    if (c.mate != null) { // blind-mate XT60PW on the power board's underside bracket (connector y/z and depth assumed)
      const cyM = (c.y0 + c.y1) / 2, czM = (c.z0 + c.z1) / 2, pw = L.boards.find((q) => q.id === 'power') || L.boards[0], pg = G.boards[pw.id];
      const x = boxAt(pg, M.xt60, c.mate - 10 - pw.p.x, cyM - 7.9 - pw.p.y, czM - 4.1 - pw.p.z, 10, 15.8, 8.2);
      boxAt(pg, M.nickel, Math.max(0, c.mate - 3 - pw.p.x), cyM - 10 - pw.p.y, czM + 4.1 - pw.p.z, 1, 20, pw.p.z - czM - 4.1);
      for (let i = 0; i < c.pogo; i++) cylZ(g, M.gold, c.x0 - 0.2, cyM + 11 + i * 2.6, czM - 0.3, 0.7, 0.6, 16).rotation.set(0, 0, Math.PI / 2);
      const ii = { ref: 'Cartridge connector', type: c.C.connector.type, sub: `mates at x ${c.mate} mm \u00b7 ${c.C.connector.note || ''}` };
      info(x, ii); portItems.push({ label: `XT60PW  cartridge mate`, obj: x, info: ii });
    }
  }
  // fan
  if (L.fan) {
    const f = L.fan, g = grp(G.fan), sz = { x: f.x1 - f.x0, y: f.y1 - f.y0, z: f.z1 - f.z0 }, ax = f.axis || 'z';
    const [fw, fd] = ax === 'z' ? [sz.x, sz.y] : ax === 'y' ? [sz.x, sz.z] : [sz.y, sz.z], fh = sz[ax]; // built flat (axis = local Z), then turned
    g.position.set(f.x0 + sz.x / 2, f.y0 + sz.y / 2, f.z0 + sz.z / 2); if (ax === 'y') g.rotation.x = -Math.PI / 2; else if (ax === 'x') g.rotation.y = Math.PI / 2;
    const s = rrect(-fw / 2, -fd / 2, fw, fd, 2); s.holes.push(circ(0, 0, Math.min(fw, fd) / 2 - 1));
    const fr = mesh(new THREE.ExtrudeGeometry(s, { depth: fh, bevelEnabled: false, curveSegments: 24 }), M.plastic, g); fr.position.z = -fh / 2;
    cylZ(g, M.plastic, 0, 0, -fh / 2 + 1, fw * 0.2, fh - 2);
    for (let i = 0; i < 7; i++) { const bl = boxAt(g, M.plastic, 0, 0, 0, fw * 0.3, 4.5, 0.6); bl.position.set(0, 0, 0); bl.rotation.set(0.45, 0, (i / 7) * Math.PI * 2); bl.geometry.translate(fw * 0.32, 0, 0); }
    info(fr, { ref: 'Fan', type: `${f.size.join(' x ')} mm`, sub: `x ${f.x0}-${f.x1}, y ${f.y0}-${f.y1}, z ${f.z0}-${f.z1} \u00b7 axis ${ax}` }); portItems.push({ label: `Fan  ${f.size.join(' x ')}`, obj: fr, info: fr.userData.info });
  }
  // speaker (faces up)
  if (L.spk) {
    const s = L.spk, g = G.spk, d = s.z1 - s.z0;
    const basket = mesh(new THREE.CylinderGeometry(s.rad, s.rad - 2, d * 0.5, 48, 1, true), M.plastic, g); basket.rotation.x = Math.PI / 2; basket.position.set(s.cx, s.cy, s.z1 - d * 0.25); basket.material = M.plastic.clone(); basket.material.side = THREE.DoubleSide;
    const cone = mesh(new THREE.CylinderGeometry(s.rad - 2.5, 6, d * 0.45, 48, 1, true), std({ color: 0x2a2b2e, roughness: 0.9, side: THREE.DoubleSide }), g); cone.rotation.x = Math.PI / 2; cone.position.set(s.cx, s.cy, s.z1 - d * 0.28);
    cylZ(g, M.ic, s.cx, s.cy, s.z1 - 0.8, 6, 0.8); cylZ(g, M.nickel, s.cx, s.cy, s.z0, 9, d * 0.42);
    info(cone, { ref: 'Speaker', type: S.external_parts.find((e) => /speaker/i.test(e.name)).name, sub: `centre x ${s.cx}, y ${s.cy}, z ${s.z0}-${s.z1}` }); portItems.push({ label: 'Speaker  40 mm', obj: cone, info: cone.userData.info });
  }
  // Qi coil
  if (L.coil) {
    const q = L.coil, d = q.z1 - q.z0, rt = canvasTex(256, 256, (g) => { g.fillStyle = '#9a9a9a'; g.fillRect(0, 0, 256, 256); for (let r = 20; r < 128; r += 3.2) { g.strokeStyle = r % 6.4 < 3.2 ? '#ffffff' : '#7a7a7a'; g.lineWidth = 2; g.beginPath(); g.arc(128, 128, r, 0, 7); g.stroke(); } }, true);
    rt.repeat.set(1 / (2 * q.rad), 1 / (2 * q.rad)); rt.offset.set(0.5, 0.5);
    cylZ(G.coil, M.ferrite, q.cx, q.cy, q.z0, q.rad, d * 0.35, 48);
    const s = new THREE.Shape().absarc(0, 0, q.rad - 0.4, 0, Math.PI * 2); s.holes.push(circ(0, 0, q.rad * 0.36));
    const cm = mesh(new THREE.ExtrudeGeometry(s, { depth: d * 0.65, bevelEnabled: false, curveSegments: 48 }), std({ color: 0xc8733a, metalness: 1, roughness: 0.35, map: rt }), G.coil);
    cm.position.set(q.cx, q.cy, q.z0 + d * 0.35);
    info(cm, { ref: 'Qi coil', type: S.external_parts.find((e) => /qi|coil/i.test(e.name)).name, sub: `centre x ${q.cx}, y ${q.cy}, z ${q.z0}-${q.z1}` }); portItems.push({ label: 'Qi coil  A11 50 mm', obj: cm, info: cm.userData.info });
  }

  // ---- highlight + tooltip
  hl = new THREE.Box3Helper(hlBox, 0xc9a44c); hl.material.depthTest = false; hl.material.transparent = true; hl.renderOrder = 999; hl.visible = false; scene.add(hl);
  let tipTimer = 0;
  function showTip(i, x, y) {
    if (!i) { tip.style.opacity = 0; hl.visible = false; canvas.style.cursor = ''; req(); return; }
    tip.replaceChildren(); const b = el('b', '', i.ref); tip.append(b, document.createTextNode(i.type || '')); if (i.sub) tip.append(el('small', '', i.sub));
    const r = wrap.getBoundingClientRect(), tw = tip.offsetWidth, th = tip.offsetHeight;
    tip.style.transform = `translate(${Math.min(Math.max(4, x + 14), r.width - tw - 4)}px,${Math.min(Math.max(4, y + 14), r.height - th - 4)}px)`; tip.style.opacity = 1;
  }
  const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
  function pickAt(px, py) {
    const r = canvas.getBoundingClientRect(); ndc.set(((px - r.left) / r.width) * 2 - 1, -((py - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(ndc, camera);
    const hit = ray.intersectObjects(st.xray > 0.5 ? pick : pick.concat(occluders), true).find((h) => h.object.visible);
    if (!hit) return null;
    let o = hit.object;
    if (o.isInstancedMesh && o.userData.parts) {
      const p = o.userData.parts[hit.instanceId]; hlBox.set(new THREE.Vector3(p.x, p.y, 0), new THREE.Vector3(p.x + p.w, p.y + p.d, p.h + 1.6)).applyMatrix4(o.matrixWorld);
      return { ref: p.label, type: '', sub: `${o.userData.board} \u00b7 ${p.zone}` };
    }
    while (o && !o.userData.info) o = o.parent;
    if (!o) return null; hlBox.setFromObject(o); return o.userData.info;
  }
  const focusItem = (it) => {
    hlBox.setFromObject(it.obj); hl.visible = true;
    const c = hlBox.getCenter(new THREE.Vector3()).project(camera), r = wrap.getBoundingClientRect();
    showTip(it.info, (c.x + 1) / 2 * r.width, (1 - c.y) / 2 * r.height); req();
  };

  // ---- controls
  const controls = new OrbitControls(camera, canvas);
  Object.assign(controls, { enableDamping: true, dampingFactor: 0.08, minDistance: 110, maxDistance: 1100, maxPolarAngle: Math.PI * 0.94, screenSpacePanning: true, rotateSpeed: 0.8, zoomSpeed: 0.9 });
  const fitDist = () => { const R = Math.hypot(out.x1 - out.x0, out.y1 - out.y0, out.z1 - out.z0) / 2 * 1.12, v = THREE.MathUtils.degToRad(camera.fov) / 2, h = Math.atan(Math.tan(v) * camera.aspect); return R / Math.sin(Math.min(v, h)); };
  const setView = (dist, az, el2) => camera.position.set(Math.sin(az) * Math.cos(el2) * dist, Math.sin(el2) * dist, Math.cos(az) * Math.cos(el2) * dist).add(controls.target);
  const AZ = 0.62, EL = 0.42; let touched = false, intro = null;
  setView(fitDist(), AZ, EL);

  // ---- state + tweens
  const gap = 0.55 * (out.z1 - out.z0), slide = Math.round((L.cart.x1 - L.cart.x0) * 0.9);
  const st = { explode: 0, cart: 0, xray: 0 }, tgt = { ...st };
  const ease = (t) => t * t * (3 - 2 * t), clamp = (t) => Math.min(1, Math.max(0, t));
  let applied = { tz: 0, tx: 0, k: 1 };
  function apply() {
    const e = ease(st.explode), cOpen = ease(clamp(st.cart * 2.2)), cs = ease(clamp((st.cart - 0.3) / 0.7)), x = ease(st.xray);
    G.body.position.z = e * ((L.coil ? L.coil.z1 : out.z1) - out.z0 + gap * 2.5); G.capL.position.x = -e * gap * 1.25; G.capR.position.x = e * gap * 1.25; G.led.position.x = -e * gap * 0.55;
    [...L.boards].sort((p, q) => p.p.z - q.p.z).forEach((q, i) => { G.lift[q.id].position.z = e * gap * i; }); G.hdr.position.z = e * gap * 0.5;
    G.spk.position.z = e * gap * 1.5; G.coil.position.z = e * gap * 1.5; G.cart.position.z = -e * gap * 1.05; G.cart.position.x = cs * slide;
    door.rotation.y = -Math.PI / 2 * cOpen;
    ground.position.y = blob.position.y = groundY - e * gap * 1.05; blob.position.y += 0.05;
    for (const [m, base, xr] of shell) { m.opacity = base + (xr - base) * x; m.depthWrite = m.opacity > 0.75; }
    bodyMesh.castShadow = capLMesh.castShadow = capRMesh.castShadow = x < 0.5;
    // keep the camera framing the parts as they move
    const tz = e * gap * 1.45, tx = cs * slide * 0.4, k = 1 + 0.62 * e + 0.25 * cs, off = camera.position.clone().sub(controls.target);
    controls.target.add(new THREE.Vector3(tx - applied.tx, tz - applied.tz, 0)); off.multiplyScalar(k / applied.k); camera.position.copy(controls.target).add(off);
    applied = { tz, tx, k };
    renderer.shadowMap.needsUpdate = true;
  }
  const DUR = 0.9;
  function stepTweens(dt) {
    let moving = false;
    for (const k in st) { const d = tgt[k] - st[k]; if (Math.abs(d) > 1e-4) { st[k] += Math.sign(d) * Math.min(Math.abs(d), reduced ? 1 : dt / DUR); moving = true; } }
    if (moving) apply(); return moving;
  }

  // ---- buttons
  const B = {};
  const mk = (id, label, fn) => { const b = el('button', '', label); b.type = 'button'; b.setAttribute('aria-pressed', 'false'); b.onclick = () => { fn(); sync(); kick(); }; bar.appendChild(b); B[id] = b; };
  mk('asm', 'Assembled', () => { tgt.explode = 0; tgt.cart = 0; });
  mk('exp', 'Exploded', () => { tgt.explode = tgt.explode ? 0 : 1; });
  mk('xray', 'X-ray', () => { tgt.xray = tgt.xray ? 0 : 1; });
  mk('cart', 'Cartridge out', () => { tgt.cart = tgt.cart ? 0 : 1; });
  function sync() { B.asm.setAttribute('aria-pressed', String(!tgt.explode && !tgt.cart)); B.exp.setAttribute('aria-pressed', String(!!tgt.explode)); B.xray.setAttribute('aria-pressed', String(!!tgt.xray)); B.cart.setAttribute('aria-pressed', String(!!tgt.cart)); }
  const pb = el('button', 'd3v-ports', 'Ports & parts'); pb.type = 'button'; pb.setAttribute('aria-expanded', 'false'); pb.setAttribute('aria-controls', list.id); bar.appendChild(pb);
  pb.onclick = () => { list.hidden = !list.hidden; pb.setAttribute('aria-expanded', String(!list.hidden)); if (!list.hidden) list.querySelector('button')?.focus(); };
  for (const it of portItems) {
    const b = el('button', '', it.label); b.type = 'button';
    b.onfocus = b.onmouseenter = () => focusItem(it); b.onblur = b.onmouseleave = () => showTip(null);
    b.onkeydown = (e) => { if (e.key === 'Escape') { list.hidden = true; pb.setAttribute('aria-expanded', 'false'); pb.focus(); } };
    list.appendChild(b);
  }
  sync();

  // ---- loop (render on demand)
  let raf = 0, timer = 0, last = 0, visible = true, dragging = false, lastInteract = performance.now();
  function req() { if (!raf && visible && !document.hidden) { clearTimeout(timer); timer = 0; raf = requestAnimationFrame(frame); } }
  const kick = () => { lastInteract = performance.now(); req(); };
  const pulsing = (now) => !reduced && now - lastInteract < 20000;
  function frame(now) {
    raf = 0; const dt = last ? Math.min(0.05, (now - last) / 1000) : 1 / 60; last = now;
    let active = stepTweens(dt);
    if (intro) { const t = Math.min(1, (now - intro.t0) / 1600), k = 1 - Math.pow(1 - t, 3); setView(intro.d * (1.45 - 0.45 * k), AZ + 0.7 * (1 - k), EL + 0.12 * (1 - k)); if (t >= 1) intro = null; active = true; }
    active = controls.update() || active;
    M.glow.emissiveIntensity = pulsing(now) ? 1.1 + 0.45 * Math.sin(now / 520) : 1.2;
    renderer.render(scene, camera);
    if (active || dragging) req(); else { last = 0; if (pulsing(now)) timer = setTimeout(req, 50); }
  }
  controls.addEventListener('change', req);
  controls.addEventListener('start', () => { dragging = true; touched = true; intro = null; kick(); });
  controls.addEventListener('end', () => { dragging = false; kick(); });

  // ---- pointer: hover / tap labels, wheel gating
  let engaged = wheelAlways, hoverEv = null, downAt = null;
  wrap.addEventListener('wheel', (e) => { if (!engaged && !e.ctrlKey && !e.metaKey) { e.stopPropagation(); hint.style.opacity = 1; setTimeout(() => (hint.style.opacity = ''), 900); } }, { capture: true, passive: true });
  canvas.addEventListener('pointerdown', (e) => { engaged = true; downAt = [e.clientX, e.clientY]; });
  wrap.addEventListener('pointerleave', () => { if (!wheelAlways) engaged = false; showTip(null); });
  canvas.addEventListener('pointermove', (e) => {
    if (e.pointerType !== 'mouse' || dragging) return;
    if (!hoverEv) requestAnimationFrame(() => { const ev = hoverEv; hoverEv = null; const r = wrap.getBoundingClientRect(), i = pickAt(ev.clientX, ev.clientY); hl.visible = !!i; canvas.style.cursor = i ? 'help' : ''; showTip(i, ev.clientX - r.left, ev.clientY - r.top); req(); });
    hoverEv = e;
  });
  canvas.addEventListener('pointerup', (e) => {
    if (!downAt || Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) > 6 || e.pointerType === 'mouse') return;
    const r = wrap.getBoundingClientRect(), i = pickAt(e.clientX, e.clientY); hl.visible = !!i; showTip(i, e.clientX - r.left, e.clientY - r.top); req();
    clearTimeout(tipTimer); tipTimer = setTimeout(() => showTip(null), 3500);
  });

  // ---- size, visibility, theme, motion preference
  new ResizeObserver(() => {
    const w = wrap.clientWidth, h = wrap.clientHeight; if (!w || !h) return;
    renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
    if (!touched && !intro) setView(fitDist() * applied.k, AZ, EL); req();
  }).observe(wrap);
  new IntersectionObserver((en) => { visible = en[0].isIntersecting; if (visible) req(); else { cancelAnimationFrame(raf); raf = 0; clearTimeout(timer); last = 0; } }).observe(wrap);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) req(); });
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', applyTheme);
  new MutationObserver(applyTheme).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme', 'class', 'style'] });
  mqReduce.addEventListener('change', () => { reduced = mqReduce.matches; if (reduced) intro = null; req(); });

  applyTheme(); apply();
  if (!reduced) intro = { t0: performance.now(), d: fitDist() };
  req();
  return { L, scene, camera };
}

/* ------------------------------------------------------------------ boot */
async function loadOrbit() {
  try { return (await import(ORBIT_URL)).OrbitControls; } catch (e) { /* bare 'three' specifier without an import map */ }
  const src = await (await fetch(ORBIT_URL)).text();
  const url = URL.createObjectURL(new Blob([src.replace(/from\s*['"]three['"]/g, `from '${THREE_URL}'`)], { type: 'text/javascript' }));
  try { return (await import(url)).OrbitControls; } finally { URL.revokeObjectURL(url); }
}
function note(host, msg) { const p = document.createElement('p'); p.className = 'd3v-note'; p.textContent = msg; host.appendChild(p); }
function hasWebGL() { try { const c = document.createElement('canvas'); return !!(window.WebGLRenderingContext && (c.getContext('webgl2') || c.getContext('webgl'))); } catch (e) { return false; } }

async function boot() {
  const host = document.getElementById('device-3d');
  if (!host || host.dataset.d3v) return; host.dataset.d3v = '1';
  if (!hasWebGL()) return note(host, 'The interactive 3D model needs WebGL, which is not available in this browser.');
  let spec = FALLBACK_SPEC;
  if (host.dataset.spec !== 'inline') {
    try { const r = await fetch(host.dataset.spec || new URL('mech_spec.json', import.meta.url), { cache: 'no-cache' }); if (r.ok) spec = await r.json(); } catch (e) { /* use the inline copy */ }
  }
  try { THREE = await import(THREE_URL); OrbitControls = await loadOrbit(); }
  catch (e) { return note(host, 'The 3D viewer could not load three.js from the CDN (offline?).'); }
  try { start(host, spec); } catch (e) { console.error('device3d:', e); note(host, 'The 3D model could not start in this browser.'); }
}
if (typeof document !== 'undefined') boot();
