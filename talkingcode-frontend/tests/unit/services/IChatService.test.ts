import { describe, it, expect } from 'vitest';
import type { IChatService } from '$lib/services/IChatService';

describe('IChatService', () => {
  it('defines the askAgentic method signature', () => {
    const service: IChatService = {
      askAgentic: async function* () {},
    };
    expect(service).toBeDefined();
  });
});
