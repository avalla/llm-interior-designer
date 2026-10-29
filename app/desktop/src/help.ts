// Help content: the guide, what each check means (thresholds from docs/design-rules.md), the plan legend, controls.
// Result rows link here by category (data-help="Seats").

export const GLOSSARY: Record<string, { what: string; rule: string }> = {
  Openings: { what: "A door or sliding leaf hits furniture, a wall or another door while it opens.",
    rule: "The leaf must sweep 0-90° (or slide fully open) without touching anything." },
  Handles: { what: "With the door open at 90°, the handle hits a wall or a piece of furniture.",
    rule: "At least 7 cm clear for the hand." },
  Reveals: { what: "The door frame is too close to the wall at its side: the leaf cannot open fully and the hand has no room.",
    rule: "At least 10 cm between the opening and the perpendicular wall." },
  Seats: { what: "Room behind a chair or stool, from the edge of the table to the first obstacle.",
    rule: "75 cm to stand up; 90 cm so that someone can walk behind a seated person." },
  Clearances: { what: "Width of a passage between two elements: kitchen aisle, bed sides, corridors.",
    rule: "Kitchen aisle 90 (comfort 110) cm; island to tall units 80/90; bed sides 60/70; main passage 80/90." },
  "Access zones": { what: "Free floor in front of a wardrobe, cabinet or appliance, to open it and stand there.",
    rule: "70 cm clear in front of the unit (light pieces such as nightstands are assumed to be moved)." },
  Routes: { what: "Every destination (sofa, bed sides, WC, wardrobes...) must be reachable from the entrance.",
    rule: "A continuous path 60 cm wide; open doors count as obstacles." },
  Privacy: { what: "Shared rooms should not be reached only through a bedroom; the WC and the bed should not be seen from the entrance.",
    rule: "Route search with private rooms blocked; sightline from the entrance with the doors open." },
  "Light and air": { what: "Daylight in habitable rooms; window or ventilation in bathrooms.",
    rule: "Glazed area at least 1/8 of the floor (indicative, DM 5/7/1975)." },
  "Brief constraints": { what: "The TV must not be above, in front of or next to a window on the same wall (glare).",
    rule: "At least 1 m from a window on the same wall; 1.5 m is better." },
  Safety: { what: "Electrical items (washing machine, towel warmer...) in the splash zone of a shower or bath.",
    rule: "No electrical item within 60 cm of an open side (check the local code)." },
  Robustness: { what: "A measure that passes by less than the placement tolerance: on site it may fail.",
    rule: "Every measure at least 4 cm above its minimum (2 × 2 cm tolerance)." },
  Geometry: { what: "Furniture drawn inside a wall or inside another piece (a chair under its table is fine).",
    rule: "No overlap except the ones a plan draws on purpose." },
  Assembly: { what: "A tall unit must be tilted up in the room when it is assembled.",
    rule: "Diagonal (height × depth) at most the room height − 2 cm." },
  Ergonomics: { what: "Height between a surface and its seat.", rule: "25-32 cm." },
};

const LEGEND: [string, string][] = [
  ["lg-wall", "Walls"], ["lg-room", "Room (private rooms darker)"], ["lg-furniture", "Furniture"],
  ["lg-front", "Front of a piece"], ["lg-zone", "Access zone"], ["lg-wet", "Splash zone"],
  ["lg-target", "Destination"], ["lg-start", "Entrance (routes start here)"], ["lg-dwg", "The drawing as it is"],
  ["lg-hl", "Selected result"],
];

export function legendHtml() {
  return LEGEND.map(([c, t]) => `<span class="lg"><i class="${c}"></i>${t}</span>`).join("");
}

export function helpHtml(focus?: string) {
  const checks = Object.entries(GLOSSARY).map(([k, v]) =>
    `<dt id="help-${k.replace(/\s/g, "-")}"${k === focus ? ' class="focus"' : ""}>${k}</dt>
     <dd>${v.what}<br><span class="muted">Rule: ${v.rule}</span></dd>`).join("");
  return `
  <h2>How it works</h2>
  <ol>
    <li><b>Open a plan</b> (DXF, or DWG with the free ODA File Converter installed). Or drag the file onto the window.</li>
    <li><b>Check what was recognised</b>: the line above the plan counts walls, rooms, doors, windows and furniture.
      If something is missing, the notes say why and what to do.</li>
    <li><b>Fix the mapping</b> if needed (tab <i>Mapping</i>): which layer holds the walls, what each furniture block is,
      which side of a block is its front. Press <i>Re-analyse</i>.</li>
    <li><b>Read the results</b> (tab <i>Results</i>): click a row to see the element on the plan.</li>
    <li><b>Save the profile</b> so the next plan of the studio is read correctly at once.</li>
  </ol>
  <p class="muted">Everything stays on this computer. The app reviews the plan; it does not move anything.
    Results are a preliminary check, not a construction document.</p>

  <h2>How the plan should be drawn</h2>
  <ul>
    <li>Walls as closed polylines or hatches, on their own layer.</li>
    <li>Doors as <b>blocks</b> with the leaf and its swing arc; sliding doors and windows as blocks.</li>
    <li>Each piece of furniture as one <b>block</b>; a block name that says what it is (ARMADIO, SOFA, LETTO...) is
      recognised at once; catalogue codes (AR01...) are typed once per family in Mapping.</li>
    <li>Room names as texts inside the rooms (CAMERA, BAGNO... make bedrooms private and bathrooms wet).</li>
    <li>Plans drawn with loose lines and arcs only are shown, but not checked yet.</li>
  </ul>

  <h2>Results</h2>
  <p><span class="chip bad">blocking</span> must be fixed · <span class="chip warn">significant</span> should be fixed ·
    <span class="chip info">below comfort</span> works, but tight.
    <i>Not verifiable</i>: the plan does not say enough (for example a bathroom without a window).</p>
  <dl>${checks}</dl>

  <h2>Mapping and confidence</h2>
  <p>Every choice the app makes has a confidence: <span class="conf high">0.8</span> from a clear name,
    <span class="conf mid">0.5</span> from what a layer contains, <span class="conf low">0.3</span> a guess.
    Choices below 0.7 are counted on the <i>Mapping</i> tab. Hover a layer in the table to see its lines on the plan.</p>

  <h2>Plan legend</h2>
  <div class="legend-list">${legendHtml()}</div>

  <h2>Controls</h2>
  <ul>
    <li>Wheel: zoom · drag: move · <kbd>F</kbd>: fit the plan · <kbd>F1</kbd> or <kbd>?</kbd>: this help ·
      <kbd>Esc</kbd>: close it.</li>
    <li>Click the line above the plan to hide or show the notes; the boxes at the bottom switch the plan layers.</li>
  </ul>`;
}
