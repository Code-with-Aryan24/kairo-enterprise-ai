const BASE_URL = "http://127.0.0.1:8000";

export async function getSystemInfo() {
  const response = await fetch(`${BASE_URL}/`);

  if (!response.ok) {
    throw new Error("Unable to connect to KAIRO backend.");
  }

  return response.json();
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${BASE_URL}/api/documents/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));

    throw new Error(
      errorData.detail || "Failed to upload document."
    );
  }

  return response.json();
}

export async function getDocuments() {
  const response = await fetch(`${BASE_URL}/api/documents`);

  if (!response.ok) {
    throw new Error("Failed to load documents.");
  }

  return response.json();
}