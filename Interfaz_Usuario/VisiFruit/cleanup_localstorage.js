// Ejecutar esto en la consola del navegador para limpiar localStorage corrupto
console.log('🧹 Limpiando localStorage de VisiFruit...');

// Limpiar configuraciones que pueden estar corruptas
localStorage.removeItem('visifruit_belt_config');
localStorage.removeItem('visifruit_stepper_config');

console.log('✅ LocalStorage limpiado. Recarga la página (F5) para que los cambios tengan efecto.');
console.log('🔄 Las configuraciones se resetearán a los valores por defecto.');
