# BizFlow database design (starter)

## Core relationships

- `auth_user` 1—N `Business` through `Business.owner`
- `Business` 1—N `Category`
- `Business` 1—N `Product`; `Category` 1—N `Product` (category optional)
- `Business` 1—N `Customer`
- `Business` 1—N `Supplier`
- `Business` 1—N `Purchase`; `Supplier` 1—N `Purchase`
- `Purchase` 1—N `PurchaseItem`; each purchase item references a `Product`
- `Business` 1—N `CustomerSale`; optional `Customer` 1—N `CustomerSale`
- `CustomerSale` 1—N `SaleItem`; each sale item references a `Product`
- `Business` 1—N `Expense`
- `Business` 1—N `StockMovement`; each movement references a `Product` and the user who performed it
- `Business` 1—N `Notification`

Django also creates authentication, permission, session and migration tables.

## Data integrity choices

- Product SKU is unique within a business.
- Category name is unique within a business.
- Invoice number is unique within a business.
- Monetary values use `DecimalField`.
- Purchases and sales use child item tables for multi-product transactions.
- Sale and purchase workflows update stock and record movements in a database transaction.
- Business-owned records include a business foreign key to support tenant scoping.
- Historical sales/purchase items protect referenced products from deletion.

## Simplified estimated profit

For the current month:

`Estimated net profit = total recorded sale totals - cost of goods sold for those sales - recorded operating expenses`

Cost of goods sold is captured on sale using the product's recorded purchase price at sale time. This is an educational approximation; a real accounting system should use an agreed inventory valuation method and reconcile returns, discounts, taxes, shipping, write-offs and outstanding payments.

## Diagram (logical)

```text
User
 └── Business
     ├── Category ── Product
     ├── Customer ── CustomerSale ── SaleItem ── Product
     ├── Supplier ── Purchase ── PurchaseItem ── Product
     ├── Expense
     ├── StockMovement ── Product
     └── Notification
```

## Follow-up schema work

For a larger version, add business memberships and staff roles, configurable tax rules, payments, sales returns, purchase returns, stock adjustments with approval, audit events, and explicit inventory valuation layers.
