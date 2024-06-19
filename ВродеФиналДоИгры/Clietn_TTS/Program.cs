using System;
using System.IO;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using NAudio.Vorbis;
using NAudio.Wave;

namespace SocketIOClientApp
{
    class Program
    {
        static async Task Main(string[] args)
        {
            Console.Write("Enter your name: ");
            string name = Console.ReadLine();

            Console.Write("Enter speaker (baya, kseniya, aidar): ");
            string speaker = Console.ReadLine();

            // Создание уникальной папки на рабочем столе для аудиофайлов клиента
            string desktopPath = Environment.GetFolderPath(Environment.SpecialFolder.Desktop);
            string clientFolderPath = Path.Combine(desktopPath, $"audio_{name}");
            Directory.CreateDirectory(clientFolderPath);

            ClientWebSocket webSocket = new ClientWebSocket();
            Uri serverUri = new Uri("ws://localhost:5000");

            try
            {
                await webSocket.ConnectAsync(serverUri, CancellationToken.None);
                Console.WriteLine("Connected to server");

                int fileIndex = 0; // Глобальный индекс для нумерации файлов

                Queue<byte[]> audioQueue = new Queue<byte[]>(); // Очередь аудиофайлов для воспроизведения
                bool isPlaying = false; // Флаг, указывающий на проигрывание аудио

                // Функция для воспроизведения аудио
                void PlayAudio(byte[] audioData)
                {
                    using (var vorbisStream = new MemoryStream(audioData))
                    using (var vorbisReader = new VorbisWaveReader(vorbisStream))
                    using (var waveOut = new WaveOutEvent())
                    {
                        waveOut.Init(vorbisReader);
                        waveOut.Play();
                        while (waveOut.PlaybackState == PlaybackState.Playing)
                        {
                            Thread.Sleep(100);
                        }
                    }
                }

                async Task ReceiveAudio()
                {
                    while (webSocket.State == WebSocketState.Open)
                    {
                        try
                        {
                            byte[] buffer = new byte[8192];
                            using (MemoryStream audioStream = new MemoryStream())
                            {
                                WebSocketReceiveResult result;
                                do
                                {
                                    result = await webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), CancellationToken.None);
                                    audioStream.Write(buffer, 0, result.Count);
                                } while (!result.EndOfMessage);

                                // Save received audio file
                                string audioFileName = $"{speaker}_{fileIndex.ToString("000")}.ogg";
                                string audioFilePath = Path.Combine(clientFolderPath, audioFileName);
                                File.WriteAllBytes(audioFilePath, audioStream.ToArray());
                                Console.WriteLine($"Saved audio file: {audioFileName}");

                                // Add audio data to queue
                                audioQueue.Enqueue(audioStream.ToArray());

                                Interlocked.Increment(ref fileIndex);
                            }

                            // Play audio if not currently playing
                            if (!isPlaying && audioQueue.Count > 0)
                            {
                                isPlaying = true;
                                while (audioQueue.Count > 0)
                                {
                                    PlayAudio(audioQueue.Dequeue());
                                }
                                isPlaying = false;
                            }
                        }
                        catch (Exception ex)
                        {
                            Console.WriteLine($"Error receiving audio: {ex.Message}");
                        }
                    }
                }

                _ = Task.Run(ReceiveAudio); // Запуск асинхронного приема аудио

                while (true)
                {
                    Console.Write("Enter message (type 'exit' to quit): ");
                    string text = Console.ReadLine();

                    if (text.ToLower() == "exit")
                        break;

                    var message = new
                    {
                        speaker = speaker,
                        text = text
                    };

                    string jsonMessage = System.Text.Json.JsonSerializer.Serialize(message);
                    byte[] bytes = Encoding.UTF8.GetBytes(jsonMessage);
                    await webSocket.SendAsync(new ArraySegment<byte>(bytes), WebSocketMessageType.Text, true, CancellationToken.None);
                    Console.WriteLine($"Sent message to server: {text}");
                }

                await webSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "", CancellationToken.None);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error: {ex.Message}");
            }
        }
    }
}
