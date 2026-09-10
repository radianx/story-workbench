// Shared by the project wizard and the current library. No state or DOM mutations.
export async function importBookFile(file, api) {
  if (
    !/\.(md|markdown|txt|epub|docx)$/i.test(file.name) ||
    file.size > 15000000
  )
    throw Error("Elegí Markdown, TXT, EPUB o DOCX de hasta 15 MB.");
  const bytes = new Uint8Array(await file.arrayBuffer());
  let binary = "";
  for (let offset = 0; offset < bytes.length; offset += 8192)
    binary += String.fromCharCode(...bytes.subarray(offset, offset + 8192));
  return api("/api/import/file", { name: file.name, data: btoa(binary) });
}
