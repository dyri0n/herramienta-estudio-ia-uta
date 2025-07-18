"use client"
import { MessageSquare, FileText, Languages, Zap } from "lucide-react"
import { useNLP } from "@/app/context/NLPContext"
import { useState } from "react"  

const services = [
  {
    id: "questions",
    name: "Generación de Preguntas",
    description: "Genera preguntas relevantes del contenido",
    icon: MessageSquare,
    color: "text-blue-600",
    endpoint: "/generator/",
    requestBody: (content: string) => ({ context: content })
  },
  {
    id: "summary",
    name: "Resumen de Texto",
    description: "Crea un resumen conciso del documento",
    icon: FileText,
    color: "text-green-600",
    endpoint: "/summarizer/",
    requestBody: (content: string) => ({ text: content })
  },
  {
    id: "translation",
    name: "Traducción EN>ES",
    description: "Traduce el contenido del inglés al español",
    icon: Languages,
    color: "text-purple-600",
    endpoint: "/translator/traducir_a_espanol/",
    requestBody: (content: string) => ({ text: content })
  },
] as const;

export default function ServiceTabs() {
  const { state, dispatch } = useNLP();
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedService, setSelectedService] = useState<string>("questions");
  
  // Usa esta ruta si configuraste el proxy en Next.js
  // const API_BASE_URL = "/api/proxy";
  // O usa esta si configuraste CORS en el backend
  const API_BASE_URL = "http://127.0.0.1:8000";

  const handleServiceChange = (serviceId: string) => {
    setSelectedService(serviceId);
    dispatch({ type: "SET_SELECTED_SERVICE", payload: serviceId });
  };

  const processDocument = async () => {
    if (!state.currentDocument?.content) {
      setError('No hay documento cargado para procesar');
      return;
    }

    setError(null);
    setIsProcessing(true);

    try {
      const service = services.find(s => s.id === selectedService);
      if (!service) throw new Error("Servicio no válido");

      // Construir el cuerpo según el servicio
      const requestBody = service.requestBody(state.currentDocument.content);
      
      console.log("Enviando solicitud a:", `${API_BASE_URL}${service.endpoint}`);
      console.log("Cuerpo de la solicitud:", requestBody);

      const response = await fetch(`${API_BASE_URL}${service.endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
        mode: 'cors'
      });

      // Verifica encabezados CORS
      console.log("Encabezados de respuesta:");
      response.headers.forEach((value, name) => {
        console.log(`${name}: ${value}`);
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Error response text:", errorText);
        
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch {
          errorData = { detail: errorText };
        }
        
        throw new Error(errorData.detail || `Error ${response.status}`);
      }

      const result = await response.json();
      console.log("Resultado recibido:", result);

      // Manejar diferentes formatos de respuesta según el servicio
      let processedResult: any;
      switch(service.id) {
        case "questions":
          // Para generador de preguntas, ahora esperamos un array de QA
          processedResult = result.qas || [];
          break;
        case "summary":
          // Para resumen, esperamos texto plano
          processedResult = result.result || result;
          break;
        case "translation":
          // Para traducción, esperamos texto traducido
          processedResult = result.translated_text || result;
          break;
        default:
          processedResult = result;
      }

      // Actualizar el documento en el contexto con el resultado
      dispatch({
        type: "UPDATE_DOCUMENT",
        payload: {
          id: state.currentDocument.id,
          updates: {
            [selectedService]: processedResult
          }
        }
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
      setError(`Error al procesar: ${errorMessage}`);
      console.error('Error completo en processDocument:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">Servicios NLP</h2>

      <div className="grid grid-cols-1 gap-4">
        {services.map((service) => {
          const Icon = service.icon
          const isSelected = selectedService === service.id

          return (
            <button
              key={service.id}
              onClick={() => handleServiceChange(service.id)}
              className={`
                p-4 rounded-lg border-2 text-left transition-all focus:outline-none focus:ring-2 focus:ring-primary-500
                ${isSelected 
                  ? "border-primary-500 bg-primary-50" 
                  : "border-gray-200 hover:border-gray-300 bg-white"}
              `}
              disabled={!state.currentDocument}
              aria-pressed={isSelected}
            >
              <div className="flex items-start space-x-3">
                <Icon className={`h-6 w-6 mt-1 ${service.color}`} />
                <div className="flex-1">
                  <h3 className={`font-medium ${isSelected ? "text-primary-900" : "text-gray-900"}`}>
                    {service.name}
                  </h3>
                  <p className={`text-sm mt-1 ${isSelected ? "text-primary-700" : "text-gray-500"}`}>
                    {service.description}
                  </p>
                </div>
              </div>
            </button>
          )
        })}
      </div>

      <button
        onClick={processDocument}
        disabled={!state.currentDocument || isProcessing}
        className="
          w-full py-3 px-4 rounded-lg font-medium 
          transition-colors duration-200
          focus:outline-none focus:ring-2 
          focus:ring-ring focus:ring-offset-2
          disabled:bg-muted disabled:text-muted-foreground disabled:cursor-not-allowed
          bg-primary text-primary-foreground 
          hover:bg-primary/90 dark:hover:bg-primary/80
          relative flex items-center justify-center
        "
      >
        {isProcessing ? (
          <>
            <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></span>
            Procesando...
          </>
        ) : (
          <>
            <Zap className="h-4 w-4 mr-2" />
            Procesar Documento
          </>
        )}
      </button>

      {error && (
        <div className="flex items-center space-x-2 text-red-600 bg-red-50 p-3 rounded-md">
          <span className="text-sm">{error}</span>
        </div>
      )}
    </div>
  )
}