# Native app implementation

Determine the platform from the project. Preserve Kotlin/Compose, Android Views/Java, SwiftUI/UIKit, React Native, or Flutter as found. Retain native navigation, input, permissions, insets, and accessibility behavior. Do not call a browser mockup a native implementation.

## Android

- Use the current Compose/View system. Expose stable UI state and events; keep durable state in the existing owner. Choose `remember`, saveable state, and ViewModel by lifetime instead of keeping everything in a composable.
- Expose meaningful semantics/descriptions for informative or actionable elements. Avoid redundant descriptions on decorative icons next to labeled text.
- Maintain non-overlapping touch regions of at least 48 dp where Android guidance applies. Visible icons may be smaller than their target; check expanded regions for overlap.
- Check system bars, IME, font scaling, back, failures, and recreation for the changed flow. Preserve drafts when promised.
- Use available Compose semantics tests, Espresso/UI tests, previews, and emulator/device execution. A preview image does not prove taps, TalkBack, keyboard access, or persistence.

## iOS, React Native, Flutter

Follow native navigation and component conventions. Check safe areas, font scaling, accessible labels/selected states, keyboard dismissal, back behavior, and reduced-motion settings. Prefer discoverable controls over custom gestures for essential actions.

Use installed native test/preview tools. Share behavioral intent with web guidance, not DOM/ARIA implementation details. Verify numerical platform requirements in current official documentation before reporting conformance.

## Evidence limits

Without a compatible SDK, emulator, simulator, or device, perform available implementation/code/build checks and identify device interaction and visual verification as unverified. Do not substitute a web screenshot for a tested native screen. Label mock-data boundaries.

Sources: [Android accessibility defaults](https://developer.android.com/develop/ui/compose/accessibility/api-defaults), [Apple accessibility guidance](https://developer.apple.com/design/human-interface-guidelines/accessibility). Open platform documentation when a specific API behavior needs verification.
