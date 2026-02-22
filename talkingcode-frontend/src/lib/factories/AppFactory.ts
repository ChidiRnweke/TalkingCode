/** App factory for dependency injection */
import { ChatController } from '$lib/controllers/ChatController';
import { ChatService } from '$lib/services/ChatService';

export class AppFactory {
	static getChatController(): ChatController {
		const chatService = new ChatService();
		return new ChatController(chatService);
	}
}
