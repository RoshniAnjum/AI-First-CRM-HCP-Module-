import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  hcp_name: '',
  interaction_type: '',
  date: '',
  time: '',
  attendees: '',
  discussion_topic: '',
  sentiment: '',
  materials_shared: '',
  brochure_shared: false,
  summary: '',
  follow_up: null,
  validation: null,
  last_tool: null,
}

const formSlice = createSlice({
  name: 'form',
  initialState,
  reducers: {
    updateForm(state, action) {
      const { form_data, follow_up, validation, tool_called } = action.payload
      if (form_data) {
        state.hcp_name         = form_data.hcp_name         ?? state.hcp_name
        state.interaction_type = form_data.interaction_type ?? state.interaction_type
        state.date             = form_data.date             ?? state.date
        state.time             = form_data.time             ?? state.time
        state.attendees        = form_data.attendees        ?? state.attendees
        state.discussion_topic = form_data.discussion_topic ?? state.discussion_topic
        state.sentiment        = form_data.sentiment        ?? state.sentiment
        state.materials_shared = form_data.materials_shared ?? state.materials_shared
        state.brochure_shared  =
          form_data.brochure_shared !== undefined
            ? form_data.brochure_shared
            : state.brochure_shared
        state.summary = form_data.summary ?? state.summary
      }
      state.follow_up  = follow_up  ?? state.follow_up
      state.validation = validation ?? state.validation
      state.last_tool  = tool_called ?? state.last_tool
    },
    clearForm(state) {
      state.hcp_name         = ''
      state.interaction_type = ''
      state.date             = ''
      state.time             = ''
      state.attendees        = ''
      state.discussion_topic = ''
      state.sentiment        = ''
      state.materials_shared = ''
      state.brochure_shared  = false
      state.summary          = ''
      state.follow_up        = null
      state.validation       = null
      state.last_tool        = 'ClearFormTool'
    },
  },
})

export const { updateForm, clearForm } = formSlice.actions
export default formSlice.reducer
