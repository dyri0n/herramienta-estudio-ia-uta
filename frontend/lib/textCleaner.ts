// En tu archivo utils/textCleaner.ts
export const cleanText = (text: string): string => {
  // Paso 1: Reemplazar saltos de línea con espacios
  let cleaned = text.replace(/\r?\n|\r/g, ' ');
  
  // Paso 2: Eliminar espacios múltiples consecutivos
  cleaned = cleaned.replace(/\s+/g, ' ');
  
  // Paso 3: Reemplazar comillas problemáticas
  cleaned = cleaned.replace(/["']/g, '');
  
  // Paso 4: Eliminar caracteres especiales problemáticos
  cleaned = cleaned.replace(/[^\w\s.,;:!?áéíóúÁÉÍÓÚñÑ¿¡-]/g, '');
  
  // Paso 5: Normalizar espacios alrededor de signos de puntuación
  cleaned = cleaned.replace(/\s+([.,;:!?])/g, '$1');  // Espacios antes
  cleaned = cleaned.replace(/([.,;:!?])\s+/g, '$1 '); // Espacios después
  
  // Paso 6: Eliminar espacios al inicio y final
  cleaned = cleaned.trim();
  
  return cleaned;
};

// Test para verificar la función
const testText = "Chapter I: Which treats of the character and pursuits of the famous  gentleman Don Quixote of La Mancha  In a village of La Mancha, the name of which I have no desire to call to  mind, there lived not long since one of   those gentlemen that keep a lance  in th e lance - rack, an old buckler, a lean hack, and a greyhound for  coursing. An olla of   rather more beef than mutton, a salad   on most  nights, scraps on Saturdays, lentils on   Fridays, and a pigeon or so extra  on Sundays, made away with three - quarters of his inc ome. The rest of it  went in a doublet of   fine cloth and velvet breeches and shoes to match  for holidays, while on week - days he made a brave figure in   his best  homespun. He had in his house a housekeeper past forty, a niece under  twenty, and a lad for the f ield and market - place, who used   to saddle the  hack as well as handle the bill - hook. The age of this gentleman of ours  was bordering on fifty; he was of a hardy habit, spare, gaunt - featured, a  very early riser and   a great sportsman.   They will have it his su rname was  Quixada or Quesada (for here there is some difference of opinion among  the authors who write on the subject), although from reasonable  conjectures it seems   plain that he was called Quexana. This, however, is  of but little importance to our tale;   it will be enough not to stray a  hair's breadth from the truth in the telling of it.\n";

//console.log("Texto original:", testText);
//console.log("Texto limpio:", cleanText(testText));