import type { ImageAsset, ImageVersion } from "../types/images";
import { API_BASE_URL, apiRequest } from "./client";

export function fetchImageAssets(
  conversationId: string,
  userId: string,
): Promise<ImageAsset[]> {
  return apiRequest(
    `/conversations/${conversationId}/image-assets?user_id=${encodeURIComponent(userId)}`,
  );
}

export function uploadImageAsset(input: {
  projectId: string;
  conversationId: string;
  userId: string;
  file: File;
}): Promise<ImageAsset> {
  const body = new FormData();
  body.set("project_id", input.projectId);
  body.set("conversation_id", input.conversationId);
  body.set("user_id", input.userId);
  body.set("file", input.file);
  return apiRequest("/image-assets", { method: "POST", body });
}

export function fetchImageVersions(
  conversationId: string,
  userId: string,
): Promise<ImageVersion[]> {
  return apiRequest(
    `/conversations/${conversationId}/image-versions?user_id=${encodeURIComponent(userId)}`,
  );
}

export function createImageVersion(input: {
  conversationId: string;
  userId: string;
  sourceAttachmentId: string;
  parentVersionId: string | null;
  prompt: string;
}): Promise<ImageVersion> {
  return apiRequest("/image-versions", {
    method: "POST",
    body: JSON.stringify({
      user_id: input.userId,
      conversation_id: input.conversationId,
      source_attachment_id: input.sourceAttachmentId,
      parent_version_id: input.parentVersionId,
      prompt: input.prompt,
    }),
  });
}

export function retryImageVersion(versionId: string, userId: string): Promise<ImageVersion> {
  return apiRequest(`/image-versions/${versionId}/retry`, {
    method: "POST",
    body: JSON.stringify({ user_id: userId }),
  });
}

export function imageContentUrl(
  attachmentId: string,
  userId: string,
  download = false,
): string {
  const params = new URLSearchParams({ user_id: userId, download: String(download) });
  return `${API_BASE_URL}/attachments/${attachmentId}/content?${params}`;
}
