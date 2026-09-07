# Reuse design decisions across changes

Load this when a change affects shared appearance, several screens, or an existing design document. For a small local correction, read the applicable decisions and record only a meaningful exception; a new document is not required.

## Find the existing authority

Inspect the project's design instructions, `DESIGN.md`, theme variants, `MASTER.md`, page overrides, token definitions, and relevant shared components. Follow the actual repository paths and naming. Do not create a parallel system just because another tool uses different filenames.

Read both the common decisions and the scoped page decisions **before each subsequent UI change**. Check referenced token symbols and components in code; a remembered path or old screenshot is not current evidence.

Resolve differences in this order:

1. Follow the user's direction and explicit repository authority, including brand and accessibility constraints.
2. Apply documented page exceptions only to their named scope and fields. Other decisions inherit the common contract. Exceptions cannot waive required accessibility or change unrelated screens.
3. Treat imported designs and search results as candidates until their fit is checked. Never automatically overwrite an existing design file, token system, or page override with an imported or generated design.

Documentation states intent; running code shows the current implementation. If they disagree, identify the conflicting decision and affected component. When authority and requested scope establish the intended change, update the relevant code and document together. Otherwise preserve existing behavior for a narrow fix and record the unresolved mismatch. Ask only when the mismatch materially changes the requested direction and available evidence cannot resolve it. Do not silently declare the newest file authoritative or regenerate the whole design system.

## Record only reusable decisions

Use the established design document. If none exists and the work needs durable shared decisions, adapt [design-contract.md](../assets/design-contract.md) into the project's documentation location. A short task note is sufficient for a one-screen change with no reusable decisions.

Connect meaning to implementation rather than collecting colors:

| Semantic role | Existing code token and location | Consuming component | Scoped exception and reason | Evidence/status |
| --- | --- | --- | --- | --- |
| Secondary text | Actual symbol and relative file path | Actual component path | Page/state only, or none | Observed code/preview; inferred intent; or proposed change |

The row is illustrative; replace it with inspected symbols. Include type roles, spacing, surfaces, motion, and states only where they matter. Use the project's token mechanism, whether CSS variables, theme objects, or native resources. Reuse equivalent existing tokens before adding one. Record why a new role differs; do not manufacture a token for every component value.

Separate **observed** facts from **inferred** intent and **proposed** decisions. A reference image can support a visual observation; it cannot establish the source site's hidden tokens or interaction behavior. Keep reference links and the inspected date beside the decision they informed.

Keep page exceptions small: page/route, affected role, reason, code location, inherited default, and a condition for revisiting the exception. A dense comparison view may use tighter row spacing while retaining the product's typography and interaction conventions. Do not copy the complete common document into every page file.

When repeated component workarounds suggest an unmet product need, use the component-variation and specification cases in [Toss design](toss-design.md). Prefer an existing supported extension that retains shared states and update paths; record a justified exception without forcing every screen into the same structure or rewriting the component API by default.

## Close the loop

After implementation, check that documented symbols resolve and the scoped components use the intended roles. Update renamed tokens, approved exceptions, and relevant evidence in the same change. For a broad token or primitive change, check a [component specimen](../assets/component-specimen.md) before rolling it through screens. Record pending decisions without turning them into established rules.

The common/page structure and document-to-token connection adapt ideas from [UI UX Pro Max and getdesign.md](sources.md#guidance-integrated-in-this-bundle). Discovery, conflict handling, and evidence status above are this bundle's workflow choices.
