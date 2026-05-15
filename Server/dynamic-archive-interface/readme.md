# 🏛️ dynamic-archive-interface

> **Secure and NDA-compliant visualization samples tailored to client requirements with comprehensive technical documentation.**

---

🌐 [Korean Version ](https://github.com/ulsidae/dev_logs/blob/main/Server/dynamic-archive-interface/%EC%82%AC%EC%9A%A9%EC%84%A4%EB%AA%85%EC%84%9C.md)

---

## 📑 Table of Contents
| Section | Description |
| :--- | :--- |
| [1. Sorting Logic](#1-sorting-logic) | Overview of metadata-driven sorting mechanisms. |
| [2. System Architecture](#2-system-architecture) | Technical implementation and core logic. |
| [3. Usage & Expansion](#3-usage--expansion) | Guide for asset management and system scaling. |

---

> [!NOTE]
> The core logic resides within `index.html` and the `images/` directory. This implementation was specifically engineered to demonstrate efficient client-side asset handling for professional portfolios.

<h2 id="1-sorting-logic">💡 1. Sorting Logic</h2>

### 1.1 Entry-Order Sorting (Default)
The interface renders items based on their index in the metadata array, allowing for intentional content prioritization.

<img src="https://github.com/ulsidae/dev_logs/blob/main/Server/dynamic-archive-interface/explain/1.PNG" height="400" />

> **Logic:** Elements follow the array sequence defined in the source code.

```javascript
const projects = [
    { folder: "000000", title: "test", size: "large", count: 1, category: "brand" },
    { folder: "210212", title: "b", size: "large", count: 1, category: "ad" },
    { folder: "123145", title: "a", size: "medium", count: 2, category: "brand" },
    { folder: "260514", title: "c", size: "normal", count: 1, category: "promotion" },
    { folder: "213403", title: "d", size: "wide", count: 1, category: "brand" }
    // Sequence: test -> b -> a -> c -> d
];
```

### 1.2 Chronological Sorting (Newest / Oldest)
The system parses the folder string (YYMMDD) into a Date object to determine the chronological order.

<img src="https://github.com/ulsidae/dev_logs/blob/main/Server/dynamic-archive-interface/explain/2.PNG" height="400" />

or

<img src="https://github.com/ulsidae/dev_logs/blob/main/Server/dynamic-archive-interface/explain/3.PNG" height="400" />

Example: 210212 (FY2021) is compared against 260514 (FY2026) to automate the timeline visualization.

---
<h2 id="2-system-architecture">💡 2. System Architecture</h2>

Built with Vanilla JS and Modern CSS, eliminating external dependencies for maximum performance and security.

- Metadata Mapping: Decouples the View from the Data. All UI components are dynamically generated via the projects array, ensuring high maintainability.

- Recursive Image Fallback: Implements an automated extension check (jpg → png → gif) to prevent broken image links in inconsistent file environments.

- Interactive UX: Features a high-performance modal with native keyboard navigation support (Arrow keys for paging, ESC for closing).

<img src="https://github.com/ulsidae/dev_logs/blob/main/Server/dynamic-archive-interface/explain/55.PNG" height="400" />

- Exception Handling: Includes a continue logic in the rendering loop to ensure grid stability even if asset counts are incorrectly specified.

---

<h2 id="3-usage--expansion">💡 Usage & Expansion</h2>

### 3.1 Uploading Assets
1.Create a new directory within /images using the YYMMDD format.

2.Store your assets numerically (e.g., 1.jpg, 2.png).
> [!IMPORTANT]
> The system reads files in sequence. 1.xxx serves as both the grid thumbnail and the entry point for the modal viewer.

### 3.2 Registering Metadata
Locate the const projects = [ array in index.html.

> [!TIP]
> Use Ctrl + F in your text editor to quickly jump to the data declaration.

```
const projects = [
{ 
  folder: "000000", // Directory name (YYMMDD)
  title: "test",    // Display title on the grid
  size: "large",    // Grid span (Options: large, normal, wide, medium)
  count: 1,         // Total number of assets in the directory
  category: "brand" // Tag for future filtering (e.g., brand, ad, promotion)
},
{ folder: "210212", title: "b", size: "large", count: 1, category: "ad" }
];
```
^ (Meta-description for data fields: 'folder' is recognized as YY/MM/DD format.)

