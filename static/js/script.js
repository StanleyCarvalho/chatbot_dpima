const input = document.getElementById('pergunta');
const chatMessages = document.getElementById('chat-messages');
const personagemImg = document.getElementById('personagem-img');
const perguntaInput = document.getElementById('pergunta');
const btnPerguntar = document.getElementById('btn-perguntar');
const aviso = document.getElementById('aviso');
const sendSound = document.getElementById('send-sound');

let vozesDisponiveis = [];

// Função para carregar vozes (alguns navegadores disparam mais de uma vez)
function carregarVozes() {
  vozesDisponiveis = window.speechSynthesis.getVoices();
  if(vozesDisponiveis.length === 0) {
    // Se não tiver vozes carregadas ainda, tentar de novo em 200ms
    setTimeout(carregarVozes, 200);
  }
}

// Escuta quando as vozes mudam (evento padrão)
window.speechSynthesis.onvoiceschanged = carregarVozes;

// Função para adicionar mensagem no chat
function adicionarMensagem(texto, tipo = 'bot') {
  const msgDiv = document.createElement('div');
  msgDiv.classList.add('msg', tipo);
  msgDiv.textContent = texto;
  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Função para falar texto com voz natural + animação do personagem
function falarComVoz(texto) {
  if (!texto.trim()) return;

  personagemImg.src = "static/personagem-falando.gif";

  const utterance = new SpeechSynthesisUtterance(texto);
  utterance.lang = 'pt-BR';

  // Busca vozes mais naturais, priorizando Google e Microsoft
  const vozNatural = vozesDisponiveis.find(v => {
    const nome = v.name.toLowerCase();
    return v.lang.startsWith('pt-BR') &&
      (nome.includes('google') || nome.includes('microsoft') || nome.includes('natural'));
  });

  if (vozNatural) {
    utterance.voice = vozNatural;
  } else {
    console.warn("Voz natural não encontrada. Usando voz padrão.");
  }

  // Ajustes para uma fala mais natural
  utterance.rate = 1;     // velocidade normal (pode ajustar 0.9~1.1)
  utterance.pitch = 1.1;  // leve aumento de pitch para naturalidade
  utterance.volume = 1;   // volume máximo

  // Quando terminar a fala, volta para imagem estática
  utterance.onend = () => {
    personagemImg.src = "static/personagem-parado.png";
  };

  utterance.onerror = () => {
    personagemImg.src = "static/personagem-parado.png";
  };

  window.speechSynthesis.speak(utterance);
}

// Função para enviar pergunta para backend
async function enviarPergunta() {
  aviso.textContent = '';
  const pergunta = perguntaInput.value.trim();
  if (!pergunta) {
    aviso.textContent = 'Digite algo antes de enviar.';
    return;
  }

  adicionarMensagem(pergunta, 'user');
  perguntaInput.value = '';
  perguntaInput.disabled = true;
  btnPerguntar.disabled = true;

  try {
    const res = await fetch('http://127.0.0.1:5000/perguntar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pergunta,
        instrucoes: "Responda de forma curta, clara e objetiva, em no máximo 2 frases."
      })
    });

    if (!res.ok) throw new Error('Erro na resposta do servidor');

    const data = await res.json();

    if (data.resposta === "Desculpe, não posso responder essa pergunta no momento.") {
      aviso.textContent = data.resposta;
    } else {
      adicionarMensagem(data.resposta, 'bot');
      falarComVoz(data.resposta);
      sendSound.play();
    }

  } catch (error) {
    aviso.textContent = 'Erro ao se conectar com o servidor.';
    console.error(error);
  } finally {
    perguntaInput.disabled = false;
    btnPerguntar.disabled = false;
    perguntaInput.focus();
  }
}

window.onload = () => {
  input.focus();
  carregarVozes(); // força o carregamento inicial das vozes
};
