import type { ChatMessage, Conversation } from "../types/domain";
import { apiRequest } from "./client";

export function fetchConversations(projectId: string, userId: string): Promise<Conversation[]> {
  return apiRequest(`/projects/${projectId}/conversations?user_id=${encodeURIComponent(userId)}`);
}

export function createConversation(
  projectId: string,
  userId: string,
  title = "新聊天",
): Promise<Conversation> {
  return apiRequest(`/projects/${projectId}/conversations`, {
    method: "POST",
    body: JSON.stringify({ user_id: userId, title }),
  });
}

export function renameConversation(
  conversationId: string,
  userId: string,
  title: string,
): Promise<Conversation> {
  return apiRequest(`/conversations/${conversationId}`, {
    method: "PATCH",
    body: JSON.stringify({ user_id: userId, title }),
  });
}

export function fetchMessages(conversationId: string, userId: string): Promise<ChatMessage[]> {
  return apiRequest(
    `/conversations/${conversationId}/messages?user_id=${encodeURIComponent(userId)}`,
  );
}

export function sendMessage(
  conversationId: string,
  userId: string,
  content: string,
): Promise<ChatMessage> {
  return apiRequest(`/conversations/${conversationId}/messages`, {
    method: "POST",
    body: JSON.stringify({ user_id: userId, content }),
  });
}
