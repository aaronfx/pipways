# Blog Media Upload Guide

## 📸 Media Upload Features

The blog system now supports **full media management** with dedicated endpoints for uploading, browsing, and managing images, videos, and documents.

## 🚀 Media Endpoints

### 1. Upload Media
```http
POST /admin/media/upload
Content-Type: multipart/form-data
Authorization: Bearer {token}

file: [binary file data]
```

**Supported File Types:**
- **Images:** JPG, PNG, GIF, WebP, SVG
- **Videos:** MP4, WebM, OGG
- **Documents:** PDF, TXT, DOC, DOCX

**Response:**
```json
{
  "success": true,
  "media_id": 123,
  "url": "/uploads/images/1234567890_photo.jpg",
  "filename": "1234567890_photo.jpg",
  "type": "image",
  "size": 245760
}
```

### 2. List All Media
```http
GET /admin/media?file_type=image
Authorization: Bearer {token}
```

**Query Parameters:**
- `file_type` (optional): Filter by `image`, `video`, or `document`

### 3. Media Browser (Paginated)
```http
GET /admin/media/browser?type=image&page=1&per_page=20
Authorization: Bearer {token}
```

**For Frontend Media Picker:**
```javascript
// Load media for editor
async function loadMediaLibrary(page = 1) {
  const response = await fetch(`/admin/media/browser?type=image&page=${page}`, {
    headers: { 'Authorization': 'Bearer ' + token }
  });
  const data = await response.json();
  return data.media; // Array of media objects
}
```

### 4. Delete Media
```http
DELETE /admin/media/123
Authorization: Bearer {token}
```

### 5. Serve Media Files
```http
GET /uploads/images/1234567890_photo.jpg
```

**Public access** - no authentication required for viewing

## 📝 Using Media in Blog Posts

### Method 1: Featured Image Upload (Direct)
When creating a blog post, you can upload the featured image directly:

```http
POST /admin/blog/posts
Content-Type: multipart/form-data
Authorization: Bearer {token}

title: "My Post"
content: "<p>Post content...</p>"
featured_image_upload: [binary image file]
status: "published"
```

### Method 2: Featured Image by URL
Use an already-uploaded image:

```http
POST /admin/blog/posts
title: "My Post"
content: "<p>Post content...</p>"
featured_image: "/uploads/images/1234567890_photo.jpg"
status: "published"
```

### Method 3: Content Images (Inline)
1. **Upload image first:**
```http
POST /admin/media/upload
file: [image file]
```

2. **Use returned URL in content:**
```json
{
  "title": "My Post",
  "content": "<p>Check this chart:</p><img src='/uploads/images/1234567890_chart.png' alt='Chart'><p>Analysis...</p>",
  "status": "published"
}
```

## 🎨 Frontend Integration Example

### Media Uploader Component
```javascript
class MediaUploader {
  constructor(apiUrl, token) {
    this.apiUrl = apiUrl;
    this.token = token;
  }

  async uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.apiUrl}/admin/media/upload`, {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + this.token
      },
      body: formData
    });

    return await response.json();
  }

  async listMedia(type = 'image', page = 1) {
    const response = await fetch(
      `${this.apiUrl}/admin/media/browser?type=${type}&page=${page}`, {
      headers: { 'Authorization': 'Bearer ' + this.token }
    });
    return await response.json();
  }

  insertIntoEditor(url, type = 'image') {
    if (type === 'image') {
      return `<img src="${url}" alt="" style="max-width:100%">`;
    } else if (type === 'video') {
      return `<video controls style="max-width:100%"><source src="${url}"></video>`;
    }
  }
}

// Usage
const uploader = new MediaUploader(API_URL, authToken);

// Upload and insert
document.getElementById('imageInput').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  const result = await uploader.uploadFile(file);

  if (result.success) {
    const html = uploader.insertIntoEditor(result.url, result.type);
    editor.insertContent(html);
  }
});
```

### Media Library Browser
```javascript
async function showMediaLibrary() {
  const { media, total_pages } = await uploader.listMedia('image', 1);

  const html = media.map(m => `
    <div class="media-item" data-url="${m.url}">
      <img src="${m.url}" alt="${m.filename}">
      <p>${m.filename}</p>
      <button onclick="selectMedia('${m.url}')">Select</button>
    </div>
  `).join('');

  document.getElementById('mediaLibrary').innerHTML = html;
}

function selectMedia(url) {
  editor.insertContent(`<img src="${url}" style="max-width:100%">`);
  closeMediaModal();
}
```

## 📁 File Storage Structure

```
project/
├── uploads/
│   ├── images/      # Blog images, featured images
│   ├── videos/      # Course videos, webinar recordings
│   └── documents/   # PDFs, trading statements
```

## ⚙️ Configuration

### File Size Limits
Currently no hard limit, but recommended:
- **Images:** Max 5MB
- **Videos:** Max 100MB
- **Documents:** Max 10MB

Add to your frontend:
```javascript
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB

if (file.size > MAX_FILE_SIZE) {
  alert('File too large. Max 5MB.');
  return;
}
```

### Security
- ✅ Only admin can upload
- ✅ File type validation
- ✅ Safe filename sanitization
- ✅ Unique filenames (timestamp prefix)
- ✅ Automatic directory creation

## 🔄 Complete Workflow Example

### Creating a Blog Post with Images

**Step 1:** Upload images
```javascript
const images = await Promise.all([
  uploader.uploadFile(chartImage),
  uploader.uploadFile(screenshotImage)
]);
// Returns: [{url: '/uploads/images/...', ...}, ...]
```

**Step 2:** Create blog post with images
```javascript
const postData = new FormData();
postData.append('title', 'EUR/USD Analysis');
postData.append('content', `
  <p>This week we saw significant movement.</p>
  <img src="${images[0].url}" alt="Chart">
  <p>Key levels shown above...</p>
  <img src="${images[1].url}" alt="Screenshot">
`);
postData.append('featured_image', images[0].url);
postData.append('meta_description', 'Technical analysis of EUR/USD');
postData.append('status', 'published');

await fetch('/admin/blog/posts', {
  method: 'POST',
  headers: { 'Authorization': 'Bearer ' + token },
  body: postData
});
```

**Step 3:** Images are served automatically
```html
<img src="https://your-api.com/uploads/images/1234567890_chart.png">
```

## 💡 Pro Tips

1. **Image Optimization:** Compress images before upload (use canvas or libraries)
2. **Lazy Loading:** Add `loading="lazy"` to images in content
3. **Alt Text:** Always include descriptive alt text for SEO
4. **Featured Images:** Use 1200x630px for optimal social sharing
5. **File Naming:** Use descriptive names, system adds timestamps automatically

## 🐛 Troubleshooting

**"File type not allowed"**
→ Check file extension matches allowed types

**"Upload fails"**
→ Check file size, network connection

**"Image not showing"**
→ Verify URL path starts with `/uploads/`

**"Permission denied"**
→ Ensure user has admin role
