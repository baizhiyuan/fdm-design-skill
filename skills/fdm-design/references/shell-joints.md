# Shell joints, split lines and edge language

Mostly engineering practice; no quantitative sources were collected for this file [U]. Numbers
here are starting points to confirm with a coupon.

## When you modify or extend an existing design

1. **Measure the reference joint before designing yours.** Lip or tongue-and-groove? Which
   part carries the tongue? Width, depth, clearance per side, chamfers, the visible gap on the
   outside. Reproduce it unless the user approves a change.
2. Keep the reference's split height and seam position. Moving a split line is a structural
   change (needs approval).
3. Keep the reference's edge treatment (fillet radius or chamfer size) on new parts.

## Split lines

- Every opening (port, vent, button) lies **entirely within one part**. An opening that
  straddles two parts shows a step, gaps unevenly and weakens both edges.
- Put split lines where the print orientation of both halves is good and where a lip can
  locate them.
- Prefer one split per shell; each extra split adds a gap and a tolerance stack.

## Lips and tongue-and-groove

- A lip or tongue locates the halves and hides the seam from the outside. Its height should
  exceed the expected gap and warp; tongue clearance per side comes from your fit coupon.
- Put a small chamfer at the tongue tip (lead-in) and at the groove mouth.
- Mind print orientation: the tongue usually stands up in Z on one half; make it at least two
  perimeters thick (see [dfam-rules.md](dfam-rules.md#line-width-and-wall-thickness)).

## Gap budget and symmetry

- Decide the visible gap on purpose (for example "0 mm nominal, ≤ 0.3 mm as printed"), then
  check it in a section view. Visible gaps nobody chose are a defect.
- Mirrored panels (left/right, front/back) stay symmetric: same vent pattern, same edge
  break, same fastener positions, unless the user approves a difference.

## Edge language

- One edge treatment across the whole enclosure: either fillets of one radius on visible
  vertical edges with chamfers on bed-facing edges, or chamfers throughout. Mixing radii and
  chamfers at random reads as unfinished.
- Bed-facing edges get chamfers (overhang rule), so choose a language where that fits.

## Review

Render the closed assembly from six sides and two isometric views, and cut sections through
each joint. Check: seams continuous, gap as budgeted, no opening crosses a seam, panels
symmetric, edges consistent.
