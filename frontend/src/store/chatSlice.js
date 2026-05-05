import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { sendMessage } from '../api/chatApi'
import { updateForm, clearForm } from './formSlice'

export const sendChatMessage = createAsyncThunk(
  'chat/sendMessage',
  async ({ message, sessionId }, { dispatch, rejectWithValue }) => {
    try {
      const response = await sendMessage(message, sessionId)
      if (response.tool_called === 'ClearFormTool') {
        dispatch(clearForm())
      } else {
        dispatch(updateForm({
          form_data: response.form_data,
          follow_up: response.follow_up,
          validation: response.validation,
          tool_called: response.tool_called,
        }))
      }
      return response
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || err.message || 'Unknown error')
    }
  }
)

const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    messages: [
      {
        id: 'welcome',
        role: 'assistant',
        content: 'Log interaction details here via chat (e.g., "Met Dr. Smith, discussed Prodo-X efficacy, positive sentiment, shared brochure") or ask for help.',
        timestamp: new Date().toISOString(),
      },
    ],
    isLoading: false,
    error: null,
  },
  reducers: {
    addUserMessage(state, action) {
      state.messages.push({
        id: Date.now().toString(),
        role: 'user',
        content: action.payload,
        timestamp: new Date().toISOString(),
      })
    },
    clearError(state) {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendChatMessage.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.isLoading = false
        const { message, tool_called, follow_up } = action.payload
        let content = message
        if (follow_up) {
          content += `\n\nFollow-up suggestion: ${follow_up}`
        }
        state.messages.push({
          id: Date.now().toString(),
          role: 'assistant',
          content,
          tool_called,
          timestamp: new Date().toISOString(),
        })
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload || 'Something went wrong'
        state.messages.push({
          id: Date.now().toString(),
          role: 'assistant',
          content: `Error: ${action.payload || 'Something went wrong. Please try again.'}`,
          isError: true,
          timestamp: new Date().toISOString(),
        })
      })
  },
})

export const { addUserMessage, clearError } = chatSlice.actions
export default chatSlice.reducer
