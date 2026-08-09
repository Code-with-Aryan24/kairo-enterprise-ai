const BASE_URL = "http://127.0.0.1:8000";

export async function getSystemInfo() {
  const response = await fetch(`${BASE_URL}/`);

  if (!response.ok) {
    throw new Error("Unable to connect to KAIRO backend.");
  }

  return response.json();
}