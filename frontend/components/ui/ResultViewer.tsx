"use client"
import { useNLP } from "@/app/context/NLPContext"
import { Clipboard, Check, Star, Bug, Info } from "lucide-react"
import { useState, useEffect } from "react"

// Tipos basados en el backend
interface QA {
  context: string;
  question: string;
  answer: string;
  quality?: number;
}

interface Result {
  id: string;
  service: string;
  result: {
    qas?: QA[];
    summary?: string;
    keywords?: string[];
    wordCount?: number;
    originalText?: string;
    translatedText?: string;
    confidence?: number;
  };
}

export default function ResultViewer() {
  const { state } = useNLP();
  const [copied, setCopied] = useState(false);
  const [debugInfo, setDebugInfo] = useState<string[]>([]);
  const [activeResult, setActiveResult] = useState<Result | null>(null);
  
  // Efecto para actualizar cuando cambien los resultados o el servicio seleccionado
  useEffect(() => {
    const debugMessages: string[] = [];
    debugMessages.push(`=== INICIO DEPURACIÓN - ${new Date().toLocaleTimeString()} ===`);
    
    if (!state) {
      debugMessages.push("Estado (state) no está definido");
      setDebugInfo(debugMessages);
      return;
    }

    debugMessages.push(`Servicio seleccionado: ${state.selectedService || "Ninguno"}`);
    debugMessages.push(`Documento actual: ${state.currentDocument?.name || "Ninguno"}`);
    
    // Buscar el último resultado para el servicio seleccionado
    const lastResult = state.results.findLast(
      (result) => result.service === state.selectedService
    );
    
    if (lastResult) {
      setActiveResult({
        id: lastResult.id,
        service: lastResult.service,
        result: lastResult.result
      });
      console.log(lastResult)
      debugMessages.push(`Resultado encontrado para servicio: ${state.selectedService}`);
    } else {
      setActiveResult(null);
      debugMessages.push("No se encontraron resultados para el servicio seleccionado");
    }
    
    debugMessages.push("=== FIN DEPURACIÓN ===");
    setDebugInfo(debugMessages);
  }, [state?.selectedService, state?.results]);
  
  // Función para copiar al portapapeles
  const copyToClipboard = () => {
    if (!activeResult) return;
    
    let textToCopy = "";
    
    if (activeResult.service === "questions" && activeResult.result?.qas) {
      textToCopy = activeResult.result.qas.map((qa: QA) => 
        `P: ${qa.question}\nR: ${qa.answer}${qa.quality ? ` (Calidad: ${Math.round(qa.quality * 100)}%)` : ''}`
      ).join('\n\n');
    } else if (activeResult.service === "summary" && activeResult.result?.summary) {
      textToCopy = activeResult.result.summary;
    } else if (activeResult.service === "translation" && activeResult.result?.translatedText) {
      textToCopy = activeResult.result.translatedText;
    }
    
    if (textToCopy) {
      navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  // Si no hay resultados
  if (!activeResult) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 h-full flex flex-col">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Resultados</h3>
          <button
            onClick={() => {
              const debugText = debugInfo.join('\n');
              navigator.clipboard.writeText(debugText);
              setCopied(true);
              setTimeout(() => setCopied(false), 2000);
            }}
            className="text-gray-500 hover:text-gray-700 flex items-center text-sm"
          >
            {copied ? (
              <>
                <Check className="h-4 w-4 mr-1" /> Copiado
              </>
            ) : (
              <>
                <Clipboard className="h-4 w-4 mr-1" /> Copiar depuración
              </>
            )}
          </button>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-lg flex-grow overflow-auto">
          <div className="flex items-start mb-4 p-3 bg-yellow-50 rounded-lg">
            <Info className="h-5 w-5 text-yellow-600 mr-2 mt-0.5" />
            <div>
              <h4 className="font-medium text-yellow-800">No se encontraron resultados</h4>
              <p className="text-sm text-yellow-700">
                {state?.selectedService 
                  ? "Procesa un documento para ver los resultados aquí." 
                  : "Selecciona un servicio para comenzar."}
              </p>
            </div>
          </div>
          
          <details className="mt-4">
            <summary className="font-medium text-gray-700 cursor-pointer flex items-center">
              <Bug className="h-4 w-4 mr-2" /> Información de Depuración
            </summary>
            <div className="bg-gray-100 p-3 rounded text-sm font-mono mt-2 max-h-48 overflow-auto">
              {debugInfo.map((line, index) => (
                <div key={index} className="mb-1">{line}</div>
              ))}
            </div>
          </details>
        </div>
      </div>
    )
  }

  console.log(activeResult)

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 h-full flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          {activeResult.service === "questions" 
            ? "Preguntas Generadas" 
            : activeResult.service === "summary" 
              ? "Resumen" 
              : "Traducción"}
        </h3>
        <div className="flex space-x-2">
          <button
            onClick={() => {
              const debugText = debugInfo.join('\n');
              navigator.clipboard.writeText(debugText);
              setCopied(true);
              setTimeout(() => setCopied(false), 2000);
            }}
            className="text-gray-500 hover:text-gray-700 flex items-center text-sm"
            title="Copiar información de depuración"
          >
            <Bug className="h-4 w-4 mr-1" />
          </button>
          <button
            onClick={copyToClipboard}
            className="text-gray-500 hover:text-gray-700 flex items-center text-sm"
          >
            {copied ? (
              <>
                <Check className="h-4 w-4 mr-1" /> Copiado
              </>
            ) : (
              <>
                <Clipboard className="h-4 w-4 mr-1" /> Copiar
              </>
            )}
          </button>
        </div>
      </div>
      
      <div className="bg-gray-50 p-4 rounded-lg flex-grow overflow-auto">
        {activeResult.service === "questions" && activeResult.result?.qas ? (
          <div className="space-y-6">
            {activeResult.result.qas.map((qa: QA, index: number) => (
              <div key={index} className="border-b pb-6 last:border-b-0 last:pb-0">
                {qa.context && (
                  <div className="mb-3 p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-700">{qa.context}</p>
                  </div>
                )}
                
                <div className="flex items-start space-x-3 mb-3">
                  <div className="bg-blue-100 p-2 rounded-full">
                    <span className="font-medium text-blue-800">Q</span>
                  </div>
                  <p className="font-medium text-gray-900">{qa.question}</p>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="bg-green-100 p-2 rounded-full">
                    <span className="font-medium text-green-800">A</span>
                  </div>
                  <p className="text-gray-700">{qa.answer}</p>
                </div>
                
                {qa.quality !== undefined && (
                  <div className="mt-3 flex items-center">
                    <Star className="h-4 w-4 text-yellow-500 fill-yellow-500 mr-1" />
                    <span className="text-sm text-gray-600">
                      Calidad: {Math.round(qa.quality * 100)}%
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : activeResult.service === "summary" ? (
          <div className="space-y-4">
            <h4 className="font-medium text-gray-900 mb-2">Resumen generado:</h4>
            <p className="text-gray-700 whitespace-pre-wrap">
              {activeResult.result?.summary || "No hay resumen disponible"}
            </p>
            
            {activeResult.result?.keywords && (
              <div className="mt-4">
                <h4 className="font-medium text-gray-900 mb-2">Palabras clave:</h4>
                <div className="flex flex-wrap gap-2">
                  {activeResult.result.keywords.map((keyword: string, idx: number) => (
                    <span key={idx} className="px-3 py-1 bg-accent-100 text-accent-800 rounded-full text-sm">
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : activeResult.service === "translation" ? (
          <div className="space-y-4">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Texto original:</h4>
              <p className="text-gray-700 bg-gray-100 p-3 rounded">
                {activeResult.result?.originalText || "No disponible"}
              </p>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Traducción:</h4>
              <p className="text-gray-700 bg-primary-50 p-3 rounded">
                {activeResult.result?.translatedText || "No disponible"}
              </p>
            </div>
            
            {activeResult.result?.confidence && (
              <div className="mt-4">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-gray-700">Confianza:</span>
                  <span className="text-sm font-medium text-gray-900">
                    {(activeResult.result.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-green-500 h-2 rounded-full" 
                    style={{ width: `${activeResult.result.confidence * 100}%` }}
                  ></div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <Info className="h-12 w-12 mx-auto mb-4" />
            <p>Tipo de resultado no reconocido</p>
          </div>
        )}
      </div>
      
      <details className="mt-4 border-t pt-4">
        <summary className="font-medium text-gray-700 cursor-pointer flex items-center">
          <Bug className="h-4 w-4 mr-2" /> Información de Depuración
        </summary>
        <div className="bg-gray-100 p-3 rounded text-sm font-mono mt-2 max-h-48 overflow-auto">
          {debugInfo.map((line, index) => (
            <div key={index} className="mb-1">{line}</div>
          ))}
        </div>
      </details>
    </div>
  )
}