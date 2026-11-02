# Page object template

Locator policy: `getByRole` / `getByTestId` first. CSS/XPath only when cited from Figma or a case row.

```ts
import { type Locator, type Page } from "@playwright/test";

/** Screen: {{wiki or Figma name}} */
export class {{PageName}}Page {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  // locators…
}
```

Cite the UI path or Figma node in a file-level comment. Do not hardcode credentials.
