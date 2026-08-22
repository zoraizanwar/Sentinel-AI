import { describe, it, expect } from 'vitest';
import { extractApiError } from '../api/client';

describe('extractApiError Utility', () => {
  it('handles generic JS Error cleanly', () => {
    const err = new Error('Connection refused');
    const result = extractApiError(err);
    expect(result.errorCode).toBe('UNKNOWN_ERROR');
    expect(result.message).toBe('Connection refused');
    expect(result.statusCode).toBe(500);
  });
});
