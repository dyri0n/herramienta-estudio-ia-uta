"use client"

import type React from "react"
import { createContext, useContext, useReducer, type ReactNode } from "react"

interface Document {
  id: string;
  name: string;
  size: number;
  type: string;
  content: string;
  uploadedAt: Date;
}

interface NLPResult {
  id: string
  documentId: string
  service: string
  result: any
  createdAt: Date
  format: "json" | "txt"
}

interface NLPState {
  documents: Document[]
  currentDocument: Document | null
  selectedService: "questions" | "summary" | "translation"
  results: NLPResult[]
  isProcessing: boolean
  history: NLPResult[]
}

type NLPAction =
  | { type: "ADD_DOCUMENT"; payload: Document }
  | { type: "SET_CURRENT_DOCUMENT"; payload: Document | null }
  | { type: "SET_SELECTED_SERVICE"; payload: "questions" | "summary" | "translation" }
  | { type: "ADD_RESULT"; payload: NLPResult }
  | { type: "SET_PROCESSING"; payload: boolean }
  | { type: "CLEAR_RESULTS" }
  | { 
      type: "UPDATE_DOCUMENT"; 
      payload: {
        id: string;
        updates: Partial<Document>;
      }
    }

const initialState: NLPState = {
  documents: [],
  currentDocument: null,
  selectedService: "questions",
  results: [],
  isProcessing: false,
  history: [],
}

function nlpReducer(state: NLPState, action: NLPAction): NLPState {
  switch (action.type) {
    case "ADD_DOCUMENT":
      return {
        ...state,
        documents: [...state.documents, action.payload],
        currentDocument: action.payload,
      }
    case "SET_CURRENT_DOCUMENT":
      return { ...state, currentDocument: action.payload }
    case "SET_SELECTED_SERVICE":
      return { ...state, selectedService: action.payload }
    case "ADD_RESULT":
      return {
        ...state,
        results: [...state.results, action.payload],
        history: [...state.history, action.payload],
      }
    case "SET_PROCESSING":
      return { ...state, isProcessing: action.payload }
    case "CLEAR_RESULTS":
      return { ...state, results: [] }
    case "UPDATE_DOCUMENT":
      return {
        ...state,
        documents: state.documents.map(doc => 
          doc.id === action.payload.id ? { ...doc, ...action.payload.updates } : doc
        ),
        currentDocument: 
          state.currentDocument?.id === action.payload.id
            ? { ...state.currentDocument, ...action.payload.updates }
            : state.currentDocument
      }
    default:
      return state
  }
}

const NLPContext = createContext<{
  state: NLPState
  dispatch: React.Dispatch<NLPAction>
} | null>(null)

export function NLPProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(nlpReducer, initialState)

  return <NLPContext.Provider value={{ state, dispatch }}>{children}</NLPContext.Provider>
}

export function useNLP() {
  const context = useContext(NLPContext)
  if (!context) {
    throw new Error("useNLP must be used within NLPProvider")
  }
  return context
}
