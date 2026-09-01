# Design System Index

95 design systems from [component.gallery](https://component.gallery/). Source data: 2026-09-01. Indexes rebuilt: 2026-09-01.

## Ecosystem Currency (as of 2026-09)

Shifts since the crawl that change how entries below should be read:

- **shadcn/ui's default primitive layer is Base UI (MUI), not Radix** — since July 2026; `npx shadcn init` scaffolds Base UI, Radix stays available via `-b radix`. Several original Radix engineers built Base UI after Radix development slowed post-WorkOS. Treat Radix entries as maintenance-mode precedent, Base UI as the active line.
- **Renames:** NextUI → HeroUI, Reakit → Ariakit, Shopify Polaris → Polaris Web (new docs site, April 2026). Reach UI is unmaintained (its own repo says so) — pattern reference only.
- **W3C Design Tokens spec shipped its first stable version (2025.10, Oct 2025)** — Format/Color/Resolver modules, OKLCH/Display-P3 support. Systems publishing spec-format tokens are directly interoperable; expect token documentation to converge on it.
- **CSS theming baseline moved:** OKLCH is the default color space in new systems (Tailwind v4 is OKLCH-native), `light-dark()` handles dual-theme values in one declaration, container queries are fully supported — component docs written against media-query-only responsiveness predate this.
- **AI-native component documentation exists as a genre:** OpenUISpec (YAML props/types for LLM consumption, the `openapi.yaml` move applied to UI) and reopt's Component Spec format (props/slots/states/anti-patterns written for agents as much as humans). Relevant to how this skill's own indexes are structured.
- AI/chat components remain absent upstream — see `references/ai-components.md` for the overlay taxonomy.


| Design System | Tech | Features |
|---------------|------|----------|
| [98.css](https://jdan.github.io/98.css/) | - CSS | - Code examples, - Open source |
| [A11Y Style Guide](https://a11y-style-guide.com/style-guide/) | - jQuery | - Code examples, - Usage guidelines, - Accessibility, - Unmaintained, - Open source |
| [Ant Design](https://ant.design/) | - React | - Code examples, - Accessibility issues, - Open source |
| [Ariakit](https://ariakit.org/) | - React | - Code examples, - Open source, - Accessibility |
| [Atlassian Design System](https://atlassian.design/) | - React | - Code examples, - Usage guidelines, - Tone of voice, - Accessibility |
| [Auro](https://auro.alaskaair.com/) | - Web Components, - Sass | - Code examples, - Usage guidelines, - Open source |
| [Aurora](https://design.gccollab.ca/) | - CSS | - Code examples, - Tone of voice, - Open source, - Unmaintained |
| [Backpack](https://www.skyscanner.design/) | - Mobile, - React | - Code examples, - Usage guidelines, - Open source, - Tone of voice |
| [Base Web](https://baseweb.design/) | - React, - CSS-in-JS | - Code examples, - Usage guidelines, - Open source |
| [BBC Global Experience Language](https://www.bbc.co.uk/gel/guidelines/category/design-patterns) | — | - Accessibility, - Usage guidelines, - Unmaintained |
| [Blueprint](https://blueprintjs.com/) | - React, - Sass | - Open source |
| [Bolt Design System](https://boltdesignsystem.com/) | - Sass, - Twig, - Web Components | - Code examples, - Tone of voice, - Open source |
| [Bootstrap](https://getbootstrap.com/) | - Sass | - Code examples, - Accessibility, - Open source |
| [Brighton & Hove City Council Website pattern library](http://design.brighton-hove.gov.uk/website-pattern-library.php?p=service-icons) | — | - Unmaintained |
| [Bulma](https://bulma.io/) | - Sass | - Code examples, - Accessibility issues, - Open source |
| [Carbon Design System](https://www.carbondesignsystem.com/) | - React, - Vanilla JS, - Angular, - Vue, - Svelte, - Web Components | - Code examples, - Usage guidelines, - Open source |
| [Cauldron](https://cauldron.dequelabs.com/) | - React, - CSS | - Code examples, - Usage guidelines, - Accessibility, - Open source |
| [Cedar](https://cedar.rei.com/) | - Vue, - Sass, - CSS Modules | - Usage guidelines, - Code examples, - Open source |
| [Chakra UI](https://chakra-ui.com/) | - React, - CSS-in-JS | - Code examples, - Open source |
| [Clarity Design System](https://clarity.design/) | - CSS, - Angular, - Web Components | - Code examples, - Usage guidelines, - Open source |
| [Coral](https://design.talend.com/) | - React | - Code examples, - Tone of voice, - Open source |
| [Crayons](https://crayons.freshworks.com/) | - Web Components | - Code examples, - Open source |
| [Decathlon Design System](https://www.decathlon.design/) | - CSS, - React, - Svelte, - Vue, - Web Components | - Usage guidelines, - Code examples, - Accessibility, - Open source |
| [Dell Design System](https://www.delldesignsystem.com/) | - Vanilla JS | - Code examples, - Usage guidelines |
| [Duet Design System](https://www.duetds.com/) | - Angular, - Vue, - React | - Code examples |
| [eBay MIND Patterns](https://ebay.gitbook.io/mindpatterns/) | — | - Accessibility, - Usage guidelines, - Open source |
| [eBay Playbook](https://playbook.ebay.com/) | - HTML, - React | - Code examples |
| [Elastic UI framework](https://eui.elastic.co/) | - React, - CSS-in-JS | - Code examples, - Open source |
| [Elisa Design System](https://designsystem.elisa.fi/9b207b2c3/p/155e65-elisa-design-system) | - React | - Usage guidelines, - Code examples, - Accessibility |
| [Evergreen](https://evergreen.segment.com/) | - React | - Open source |
| [Flowbite](https://flowbite.com/) | - Tailwind CSS | - Open source, - Code examples |
| [Fluent UI](https://developer.microsoft.com/en-us/fluentui#/) | - React, - Web Components, - Mobile | - Usage guidelines, - Code examples, - Accessibility, - Open source |
| [Forma 36](https://f36.contentful.com/) | - React, - CSS-in-JS | - Code examples, - Open source |
| [FutureLearn design system](https://design-system.futurelearn.com/) | - React | - Usage guidelines, - Tone of voice |
| [Geist Design System](https://vercel.com/geist) | - React | - Code examples |
| [generic-components](https://genericcomponents.netlify.app/index.html) | - Web Components | - Code examples, - Accessibility, - Open source |
| [Gestalt](https://gestalt.pinterest.systems/) | - React, - CSS | - Code examples, - Open source, - Usage guidelines |
| [giffgaff design system](https://www.giffgaff.design/) | — | - Usage guidelines, - Code examples |
| [GOLD Design System](https://gold.designsystemau.org/) | - React, - Sass | - Code examples, - Usage guidelines, - Accessibility, - Open source, - Unmaintained |
| [GOV.UK Design System](https://design-system.service.gov.uk/) | - Nunjucks | - Code examples, - Usage guidelines, - Research, - Open source |
| [Grommet](https://v2.grommet.io/) | - React | - Code examples, - Open source |
| [Headless UI](https://headlessui.com/) | - React, - Vue | - Code examples, - Accessibility, - Open source |
| [Helios](https://helios.hashicorp.design/) | - Ember, - Sass | - Code examples, - Usage guidelines, - Accessibility, - Open source |
| [Helsinki Design System](https://hds.hel.fi/) | - React, - CSS | - Code examples, - Usage guidelines, - Accessibility, - Open source |
| [HeroUI](https://www.heroui.com/) | - React, - Tailwind CSS | - Code examples, - Open source |
| [Inclusive Components](https://inclusive-components.design/) | — | - Code examples, - Accessibility, - Unmaintained |
| [Instructure-UI](https://instructure.design/) | - React, - CSS-in-JS | - Code examples, - Accessibility, - Open source |
| [Jøkul Designsystem](https://jokul.fremtind.no/) | - React, - Sass | - Code examples, - Usage guidelines, - Open source |
| [Lightning Design System](https://www.lightningdesignsystem.com/) | - React | - Code examples, - Usage guidelines, - Tone of voice, - Open source |
| [Material Design](https://m3.material.io/) | - Mobile, - Web Components, - Sass | - Usage guidelines, - Open source, - Accessibility |
| [Momentum Design](https://momentum.design/) | - React, - Web Components | - Usage guidelines, - Open source |
| [Morningstar Product System](https://design.morningstar.com/systems/product) | - Vue | - Usage guidelines |
| [Mozilla Protocol](https://protocol.mozilla.org/) | - Handlebars, - Sass | - Usage guidelines, - Open source |
| [Nessie](https://design.ns.nl/4a05a30ad/p/04b3ac-nessie--ns-design-system) | - Web Components, - Tailwind CSS | - Usage guidelines, - Code examples |
| [NewsKit](https://www.newskit.co.uk/) | - React, - CSS-in-JS | - Code examples, - Usage guidelines, - Open source |
| [NHS Digital service manual](https://service-manual.nhs.uk/) | - Nunjucks | - Code examples, - Usage guidelines, - Research, - Tone of voice, - Open source |
| [No Style Design System](https://nostyle.onrender.com/) | - Sass, - jQuery | - Open source, - Unmaintained |
| [Nord Design System](https://nordhealth.design/) | - Web Components | - Code examples, - Usage guidelines |
| [Nucleus Design System](https://britishgas.design/) | - Web Components | - Usage guidelines |
| [ONS Design System](https://ons-design-system.netlify.app/) | - HTML, - Nunjucks, - Sass | - Code examples, - Usage guidelines, - Accessibility, - Open source |
| [Ontario Design System](https://designsystem.ontario.ca/) | - HTML, - Sass | - Code examples, - Usage guidelines, - Accessibility |
| [Orbit](https://orbit.kiwi/) | - React, - CSS-in-JS | - Usage guidelines, - Open source, - Code examples, - Tone of voice |
| [Pajamas](https://design.gitlab.com/) | - Vue | - Usage guidelines, - Code examples, - Open source |
| [Paste](https://paste.twilio.design/) | - React, - CSS-in-JS | - Usage guidelines, - Code examples, - Tone of voice, - Accessibility, - Open source |
| [PatternFly](https://www.patternfly.org/) | - React, - Sass | - Tone of voice, - Open source, - Usage guidelines |
| [Pharos](https://pharos.jstor.org/) | - Web Components, - Sass | - Usage guidelines, - Open source, - Code examples, - Accessibility, - Tone of voice |
| [Polaris](https://shopify.dev/docs/api/app-home/web-components) | - Web Components | - Code examples, - Usage guidelines, - Accessibility, - Tone of voice |
| [Porsche Design System](https://designsystem.porsche.com/v3/) | - Web Components, - Angular, - React, - Vue | - Code examples, - Open source |
| [Primer](https://primer.style/design/) | - React | - Code examples, - Open source |
| [Purple3](https://design.herokai.com/purple3) | - CSS | - Code examples, - Unmaintained |
| [Quasar Framework](https://quasar.dev/) | - Vue | - Accessibility issues, - Code examples, - Open source |
| [Radix Primitives](https://radix-ui.com/) | - React | - Code examples, - Open source |
| [Reach UI](https://reach.tech/) | - React | - Accessibility, - Code examples, - Open source |
| [Red Hat design system](https://ux.redhat.com/) | - Web Components | - Code examples, - Usage guidelines |
| [Ruter Components](https://components.ruter.as/) | - React | - Code examples, - Unmaintained |
| [Sainsbury's Design System](https://design-systems.sainsburys.co.uk/) | - React, - Sass | - Usage guidelines, - Code examples, - Tone of voice |
| [SEB Design Library](https://designlibrary.sebgroup.com/) | - Sass, - React, - Angular | - Code examples, - Usage guidelines |
| [Seeds](https://sproutsocial.com/seeds/) | - React | - Code examples, - Usage guidelines, - Tone of voice |
| [Seek style guide](https://seek-oss.github.io/seek-style-guide/) | - React | - Code examples, - Unmaintained |
| [shadcn/ui](https://ui.shadcn.com/) | - React, - Tailwind CSS | - Code examples, - Open source |
| [Shoelace](https://shoelace.style/) | - Web Components | - Code examples, - Open source |
| [Source](https://theguardian.design/2a1e5182b/p/300696-) | - React | - Code examples, - Usage guidelines, - Open source |
| [Spectrum](https://spectrum.adobe.com/) | - CSS, - Web Components, - React | - Code examples, - Usage guidelines, - Tone of voice, - Open source |
| [Stacks](https://stackoverflow.design/) | - Stimulus | - Code examples, - Usage guidelines, - Tone of voice, - Open source |
| [SubZero](https://www.subzero.axis.bank.in/) | — | - Accessibility issues |
| [Thumbprint](https://thumbprint.design/) | - React, - Sass | - Code examples, - Open source |
| [United States Web Design System](https://designsystem.digital.gov/) | - Nunjucks | - Code examples, - Usage guidelines, - Open source |
| [uStyle](https://ustyle.guide/) | - Sass | - Tone of voice, - Code examples, - Usage guidelines, - Open source, - Unmaintained |
| [Visa Product Design System](https://design.visa.com/welcome/) | - Angular, - React, - CSS, - Mobile | - Code examples, - Usage guidelines, - Accessibility, - Open source |
| [W3C design system](https://design-system.w3.org/) | - Sass, - Vanilla JS | - Code examples, - Usage guidelines, - Open source, - Accessibility |
| [Wanda](https://design.wonderflow.ai/) | - React, - CSS Modules | - Code examples, - Open source |
| [Web Awesome](https://webawesome.com/) | - Web Components | - Open source, - Code examples |
| [West Midlands Network Design System](https://designsystem.tfwm.org.uk/) | - HTML, - Nunjucks, - Sass | - Code examples, - Usage guidelines, - Open source |
| [Wise Design](https://wise.design/) | - Mobile | - Usage guidelines, - Tone of voice |
| [Workday Canvas Design System](https://design.workday.com/) | - React | - Usage guidelines, - Accessibility, - Tone of voice, - Open source |
