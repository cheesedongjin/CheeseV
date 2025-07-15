# Sitemap Submission Issue on Google Search Console

*2025-07-15*

## Problem Situation

* When submitting `sitemap.xml` to Google Search Console, the status displayed changed from **Pending** to **Sitemap could not be read**.
* Initially suspected a malformed or inaccessible sitemap file.
* Community experts have confirmed that the new console’s “couldn’t fetch” message is a bug, and **Pending** remains the true status.
* To verify accessibility:

  * **Command‑line check**

    ```bash
    # Replace with your actual domain and path
    curl -I https://your-domain.com/path/to/sitemap.xml
    HTTP/1.1 200 OK
    ```

    * Expect a **200 OK** response.
    * If you see a different status code (e.g., `404 Not Found`, `301 Moved Permanently`), double‑check that the sitemap file exists at the specified path.
    * To follow redirects and ensure there aren’t unexpected hops, you can also use:

      ```bash
      curl -I -L https://your-domain.com/path/to/sitemap.xml
      ```

      and confirm that the **final** response is **200 OK** and that no unwanted redirects occur.

  * **robots.txt check**

    * If you maintain a `robots.txt` file, ensure it does **not** contain a `Disallow` rule blocking your sitemap, for example:

      ```
      Disallow: /path/to/sitemap.xml
      ```
    * If you don’t have a `robots.txt`, you can safely skip this step.

  * **XML structure validation**

    * To rule out formatting or schema errors in your sitemap, you can paste its URL into an online validator such as:
      [https://www.xml-sitemaps.com/validate-xml-sitemap.html](https://www.xml-sitemaps.com/validate-xml-sitemap.html)
    * This tool will flag any missing tags, invalid URLs, or other well-formedness issues.

## Additional Information

* If the error persists beyond 24–48 hours, re‑inspect using URL Inspection in Search Console and revisit server or GitHub Pages settings.
