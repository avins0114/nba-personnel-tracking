# Project Webpage Guide

## Overview

The project webpage (`project_webpage.html`) is a comprehensive HTML document that includes all required sections for your course project submission.

## Sections Included

✅ **Motivation** - Problem statement and why this matters  
✅ **Approach** - Technical approach, metrics, architecture  
✅ **Implementation** - Project structure, classes, algorithms  
✅ **Results** - Findings, metric ranges, visualizations  
✅ **Problems Encountered** - Detailed discussion of challenges  
✅ **Interesting Findings** - Key insights and comparisons  
✅ **Download** - Source code and documentation links  
✅ **Future Work** - Potential improvements  

## How to Use

### Option 1: Open Directly
Simply open `project_webpage.html` in any web browser:
```bash
open project_webpage.html  # macOS
# or
xdg-open project_webpage.html  # Linux
```

### Option 2: Serve Locally
Use Python's built-in server:
```bash
python3 -m http.server 8000
```
Then open: http://localhost:8000/project_webpage.html

## Customization

### Adding Images
Replace the image placeholders with actual screenshots:
1. Take screenshots of your visualizations
2. Save them in a `images/` folder
3. Update the `<div class="image-placeholder">` sections with:
   ```html
   <img src="images/screenshot1.png" alt="Court visualization" style="max-width: 100%;">
   ```

### Adding Video
The webpage already references `avinash_akshay_566_final.mov`. Make sure:
1. The video file is in the same directory as the HTML
2. Or update the path in the `<video>` tag

### Adding Download Links
Update the download section with actual links:
```html
<a href="https://github.com/yourusername/nba-personnel-tracking/archive/refs/heads/main.zip">
    📦 Download Source Code (ZIP)
</a>
```

## Before Submission

1. ✅ Replace all image placeholders with actual screenshots
2. ✅ Verify video link works
3. ✅ Update download links with actual repository URL
4. ✅ Add any additional results or findings
5. ✅ Proofread all content
6. ✅ Test in multiple browsers (Chrome, Firefox, Safari)

## Required Elements Checklist

- [x] Motivation section
- [x] Approach section
- [x] Implementation details
- [x] Results with metrics
- [x] Problems encountered discussion
- [x] Interesting findings/comparisons
- [x] Downloadable source code section
- [x] Professional formatting
- [ ] Actual screenshots/images (add these)
- [ ] Working video link (verify)
- [ ] Actual download links (update)

## Styling

The webpage uses:
- Clean, professional design
- Responsive layout (works on mobile)
- Color-coded sections
- Easy navigation
- Print-friendly

You can customize colors, fonts, or layout by editing the `<style>` section in the HTML file.

## Notes

- The webpage is self-contained (all CSS is inline)
- No external dependencies required
- Works offline
- Can be hosted on GitHub Pages, Netlify, or any web server


