// OllamaManagerEditor.cs
// Editor window that launches start_pne.bat, stops the server,
// and pings qwen2.5:3b to verify it responds.
//
// Usage: PNE → Ollama Manager (top menu)
// Place in any Editor/ folder inside your Unity Assets/.

#if UNITY_EDITOR

using System;
using System.Diagnostics;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using UnityEditor;
using UnityEngine;
using Debug = UnityEngine.Debug;

namespace PNE.Editor
{
    public class OllamaManagerEditor : EditorWindow
    {
        const string BAT_PATH      = @"D:\Programming\PNE (Github)\cs3ip\Models\start_pne.bat";
        const string OLLAMA_URL    = "http://localhost:11434";
        const string MODEL_NAME    = "qwen2.5:3b";

        static readonly HttpClient _http = new HttpClient { Timeout = TimeSpan.FromSeconds(10) };

        string _pingResult = "";
        bool   _pinging    = false;

        [MenuItem("PNE/Ollama Manager")]
        public static void ShowWindow()
        {
            var win = GetWindow<OllamaManagerEditor>("Ollama Manager");
            win.minSize = new Vector2(340, 180);
        }

        void OnGUI()
        {
            GUILayout.Label("PNE · Ollama Manager", EditorStyles.boldLabel);
            EditorGUILayout.Space(6);

            EditorGUILayout.HelpBox(BAT_PATH, MessageType.None);
            EditorGUILayout.Space(4);

            // Row 1: Start / Stop
            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("Start PNE Server", GUILayout.Height(32)))
                LaunchBat();
            if (GUILayout.Button("Stop Server", GUILayout.Height(32)))
                StopServer();
            EditorGUILayout.EndHorizontal();

            EditorGUILayout.Space(4);

            // Row 2: Ping Model
            GUI.enabled = !_pinging;
            if (GUILayout.Button("Ping Model  (qwen2.5:3b)", GUILayout.Height(28)))
                PingModelAsync();
            GUI.enabled = true;

            if (!string.IsNullOrEmpty(_pingResult))
            {
                var isOk = _pingResult.StartsWith("OK");
                EditorGUILayout.HelpBox(_pingResult, isOk ? MessageType.Info : MessageType.Warning);
            }
        }

        // ── Start ─────────────────────────────────────────────────────────────

        static void LaunchBat()
        {
            if (!File.Exists(BAT_PATH))
            {
                Debug.LogError($"[OllamaManager] Bat file not found: {BAT_PATH}");
                return;
            }

            Process.Start(new ProcessStartInfo
            {
                FileName        = "cmd.exe",
                Arguments       = $"/k \"{BAT_PATH}\"",
                UseShellExecute = true,
                CreateNoWindow  = false,
            });

            Debug.Log("[OllamaManager] Launched start_pne.bat");
        }

        // ── Stop ──────────────────────────────────────────────────────────────

        static void StopServer()
        {
            KillByName("uvicorn");
            KillByName("ollama");
            Debug.Log("[OllamaManager] Sent kill to uvicorn + ollama processes.");
        }

        static void KillByName(string name)
        {
            try
            {
                Process.Start(new ProcessStartInfo
                {
                    FileName               = "taskkill",
                    Arguments              = $"/F /IM {name}.exe",
                    UseShellExecute        = false,
                    CreateNoWindow         = true,
                    RedirectStandardOutput = true,
                    RedirectStandardError  = true,
                });
            }
            catch (Exception ex)
            {
                Debug.LogWarning($"[OllamaManager] Could not kill {name}: {ex.Message}");
            }
        }

        // ── Ping ──────────────────────────────────────────────────────────────

        async void PingModelAsync()
        {
            _pinging   = true;
            _pingResult = "Pinging...";
            Repaint();

            try
            {
                var body = $"{{\"model\":\"{MODEL_NAME}\",\"prompt\":\"hi\",\"stream\":false}}";
                var content = new StringContent(body, Encoding.UTF8, "application/json");
                var resp = await _http.PostAsync($"{OLLAMA_URL}/api/generate", content);

                if (resp.IsSuccessStatusCode)
                {
                    var json     = await resp.Content.ReadAsStringAsync();
                    var response = ExtractJsonString(json, "response");
                    _pingResult  = $"OK — Model replied: \"{response.Trim()}\"";
                    Debug.Log($"[OllamaManager] Ping response: {response.Trim()}");
                }
                else
                {
                    _pingResult = $"HTTP {(int)resp.StatusCode} — server reachable but request failed.";
                    Debug.LogWarning($"[OllamaManager] Ping failed: {resp.StatusCode}");
                }
            }
            catch (TaskCanceledException)
            {
                _pingResult = "Timed out — is Ollama running?";
                Debug.LogWarning("[OllamaManager] Ping timed out.");
            }
            catch (Exception ex)
            {
                _pingResult = $"Error: {ex.Message}";
                Debug.LogError($"[OllamaManager] Ping error: {ex.Message}");
            }

            _pinging = false;
            Repaint();
        }

        static string ExtractJsonString(string json, string key)
        {
            var search = $"\"{key}\":";
            var idx    = json.IndexOf(search, StringComparison.Ordinal);
            if (idx < 0) return "";
            var start = idx + search.Length;
            if (start >= json.Length || json[start] != '"') return "";
            start++;
            var end = json.IndexOf('"', start);
            return end < 0 ? "" : json.Substring(start, end - start);
        }
    }
}

#endif
