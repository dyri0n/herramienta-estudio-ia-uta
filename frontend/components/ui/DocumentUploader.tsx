"use client"

import { useCallback, useState } from "react"
import { useDropzone } from "react-dropzone"
import { Upload, File, X, AlertCircle } from "lucide-react"
import { useNLP } from "@/app/context/NLPContext"
import * as pdfjsLib from 'pdfjs-dist';
import mammoth from 'mammoth';

// Agregar esta función si no existe en tu código
const parsePptx = async (arrayBuffer: ArrayBuffer): Promise<any[]> => {
  // Implementación simulada para PPTX
  return [{ content: [{ type: 'text', text: 'Texto extraído de PPTX' }] }];
};

const ACCEPTED_TYPES = {
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
  "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"],
}

const MAX_SIZE = 10 * 1024 * 1024 // 10MB

const extractTextFromFile = async (file: File): Promise<string> => {
  switch (file.type) {
    case 'application/pdf':
      return extractTextFromPdf(file);
    case 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
      return extractTextFromDocx(file);
    case 'application/vnd.openxmlformats-officedocument.presentationml.presentation':
      return extractTextFromPptx(file);
    default:
      throw new Error('Formato de archivo no soportado');
  }
};

const extractTextFromPdf = async (file: File): Promise<string> => {
  try {
    const arrayBuffer = await file.arrayBuffer();
    
    // Configura el worker
    pdfjsLib.GlobalWorkerOptions.workerSrc = 
      `//cdn.jsdelivr.net/npm/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.js`;
    
    const pdf = await pdfjsLib.getDocument(arrayBuffer).promise;
    
    let text = '';
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      text += content.items.map((item: any) => item.str).join(' ') + '\n';
    }
    
    return text;
  } catch (error) {
    console.error('Error procesando PDF:', error);
    throw new Error('Error al extraer texto del PDF');
  }
};

const extractTextFromDocx = async (file: File): Promise<string> => {
  const arrayBuffer = await file.arrayBuffer();
  const result = await mammoth.extractRawText({ arrayBuffer });
  return result.value;
};

const extractTextFromPptx = async (file: File): Promise<string> => {
  const arrayBuffer = await file.arrayBuffer();
  const slides = await parsePptx(arrayBuffer);

  let text = '';
  for (const slide of slides) {
    for (const element of slide.content) {
      if (element.type === 'text') {
        text += element.text + '\n';
      }
    }
  }
  return text;
};

export default function DocumentUploader() {
  const { state, dispatch } = useNLP()
  const [error, setError] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false);

  const onDrop = useCallback(
    async (acceptedFiles: File[], rejectedFiles: any[]) => {
      setError(null);
      setIsProcessing(true);

      if (rejectedFiles.length > 0) {
        const rejection = rejectedFiles[0];
        if (rejection.errors[0].code === "file-too-large") {
          setError(`El archivo es demasiado grande. Máximo permitido: ${formatFileSize(MAX_SIZE)}`);
        } else if (rejection.errors[0].code === "file-invalid-type") {
          setError("Formato de archivo no soportado");
        } else {
          setError("Error al subir el archivo");
        }
        setIsProcessing(false);
        return;
      }

      if (acceptedFiles.length > 0) {
        try {
          const file = acceptedFiles[0];
          const textContent = await extractTextFromFile(file);

          dispatch({ 
            type: "ADD_DOCUMENT", 
            payload: {
              id: Date.now().toString(),
              name: file.name,
              size: file.size,
              type: file.type,
              content: textContent,
              uploadedAt: new Date(),
            }
          });
        } catch (err) {
          setError(`Error al procesar: ${(err as Error).message}`);
        } finally {
          setIsProcessing(false);
        }
      }
    },
    [dispatch]
  );

  const removeDocument = () => {
    dispatch({ type: "SET_CURRENT_DOCUMENT", payload: null })
    dispatch({ type: "CLEAR_RESULTS" })
    setError(null)
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_SIZE,
    multiple: false,
  })

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Subir Documento</h2>

      {!state.currentDocument ? (
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
            ${
              isDragActive
                ? "border-primary-500 bg-primary-50"
                : "border-gray-300 hover:border-primary-400 hover:bg-gray-50"
            }
          `}
          role="button"
          tabIndex={0}
          aria-label="Área de subida de archivos"
        >
          <input {...getInputProps()} />
          <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <p className="text-lg font-medium text-gray-900 mb-2">
            {isDragActive ? "Suelta el archivo aquí" : "Arrastra un archivo o haz clic"}
          </p>
          <p className="text-sm text-gray-500 mb-4">PDF, DOCX, PPTX hasta 10MB</p>
          <button
            type="button"
            className="
              bg-primary text-primary-foreground 
              hover:bg-primary/90 
              dark:hover:bg-primary/80
              inline-flex items-center px-4 py-2 
              text-sm font-medium rounded-md 
              transition-colors duration-200
              focus-visible:outline-none focus-visible:ring-2 
              focus-visible:ring-ring focus-visible:ring-offset-2
              disabled:opacity-50 disabled:pointer-events-none
            "
          >
            Seleccionar archivo
          </button>
        </div>
      ) : (
        <div className="border rounded-lg p-4 bg-white space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <File className="h-8 w-8 text-primary-500" />
              <div>
                <p className="font-medium text-gray-900">{state.currentDocument.name}</p>
                <p className="text-sm text-gray-500">
                  {formatFileSize(state.currentDocument.size)} • Subido{" "}
                  {state.currentDocument.uploadedAt.toLocaleTimeString()}
                </p>
              </div>
            </div>
            <button
              onClick={removeDocument}
              className="p-1 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
              aria-label="Eliminar documento"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="flex items-center space-x-2 text-red-600 bg-red-50 p-3 rounded-md">
          <AlertCircle className="h-5 w-5" />
          <span className="text-sm">{error}</span>
        </div>
      )}
    </div>
  )
}