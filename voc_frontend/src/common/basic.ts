// basic utils

export enum JobStatus {
    NotStarted = 'notStarted',
    Doing = 'doing',
    Done = 'done'
}

export function playWord(word: string) {
    const utterance = new SpeechSynthesisUtterance(word);
    speechSynthesis.speak(utterance);
}