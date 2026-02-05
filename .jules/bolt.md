## 2024-05-23 - Invoice List N+1
**Learning:** The invoice list view suffered from a classic N+1 problem where fetching the airline for each invoice triggered a separate query. This is common when accessing relationships in a loop within Jinja templates.
**Action:** Use `joinedload` or `subqueryload` in the route handler to eager load relationships that are accessed in the list view template.
