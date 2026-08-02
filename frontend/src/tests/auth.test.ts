import { loginApi, registerApi } from '@/lib/auth'

describe('Authentication API Functions', () => {
  it('loginApi should return mocked token and user', async () => {
    const payload = {
      email: 'test@example.com',
      password: 'password123'
    }
    
    const result = await loginApi(payload)
    
    expect(result).toEqual({
      token: 'mock-jwt-token',
      user: {
        name: 'test',
        email: 'test@example.com'
      }
    })
  })

  it('registerApi should return mocked token and user', async () => {
    const payload = {
      name: 'John Doe',
      email: 'john@example.com',
      password: 'password123'
    }
    
    const result = await registerApi(payload)
    
    expect(result).toEqual({
      token: 'mock-jwt-token',
      user: {
        name: 'John Doe',
        email: 'john@example.com'
      }
    })
  })
})