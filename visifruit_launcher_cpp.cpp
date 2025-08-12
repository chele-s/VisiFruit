/**
 * VisiFruit Launcher - Versión C++ Nativa
 * ========================================
 * 
 * Launcher nativo en C++ con interfaz Windows API para máximo rendimiento.
 * Características:
 * - Interfaz nativa de Windows
 * - Inicio rápido
 * - Bajo consumo de memoria
 * - Integración completa con el sistema
 * 
 * Compilar con:
 * g++ -std=c++17 -static -mwindows visifruit_launcher_cpp.cpp -o VisiFruit_Launcher_Native.exe -lcomctl32 -lshell32 -luser32 -lkernel32 -lgdi32 -lws2_32 -lwininet
 * 
 * Autor: Asistente IA para VisiFruit
 * Versión: 1.0.0
 */

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <commctrl.h>
#include <shellapi.h>
#include <wininet.h>
#include <string>
#include <vector>
#include <map>
#include <thread>
#include <chrono>
#include <sstream>
#include <iostream>
#include <fstream>

#pragma comment(lib, "comctl32.lib")
#pragma comment(lib, "shell32.lib")
#pragma comment(lib, "user32.lib")
#pragma comment(lib, "kernel32.lib")
#pragma comment(lib, "gdi32.lib")
#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "wininet.lib")

// IDs de controles
#define ID_START_ALL        1001
#define ID_STOP_ALL         1002
#define ID_START_BACKEND    1003
#define ID_START_FRONTEND   1004
#define ID_START_SYSTEM     1005
#define ID_OPEN_FRONTEND    1006
#define ID_OPEN_BACKEND     1007
#define ID_OPEN_SYSTEM      1008
#define ID_LOGS_TEXTBOX     1009
#define ID_STATUS_BACKEND   1010
#define ID_STATUS_FRONTEND  1011
#define ID_STATUS_SYSTEM    1012

// Timer IDs
#define TIMER_STATUS_UPDATE 2001

class VisiFruitLauncher {
private:
    HWND hwnd;
    HWND hLogsTextBox;
    HWND hStatusBackend;
    HWND hStatusFrontend;
    HWND hStatusSystem;
    
    HBRUSH hBrushBackground;
    HBRUSH hBrushGreen;
    HBRUSH hBrushRed;
    
    std::map<std::string, bool> serviceStatus;
    std::vector<PROCESS_INFORMATION> processes;
    
public:
    VisiFruitLauncher() {
        serviceStatus["backend"] = false;
        serviceStatus["frontend"] = false;
        serviceStatus["system"] = false;
        
        // Crear brushes para colores
        hBrushBackground = CreateSolidBrush(RGB(43, 43, 43));  // Gris oscuro
        hBrushGreen = CreateSolidBrush(RGB(76, 175, 80));      // Verde
        hBrushRed = CreateSolidBrush(RGB(244, 67, 54));        // Rojo
    }
    
    ~VisiFruitLauncher() {
        DeleteObject(hBrushBackground);
        DeleteObject(hBrushGreen);
        DeleteObject(hBrushRed);
        
        // Limpiar procesos
        for (auto& process : processes) {
            if (process.hProcess != INVALID_HANDLE_VALUE) {
                TerminateProcess(process.hProcess, 0);
                CloseHandle(process.hProcess);
                CloseHandle(process.hThread);
            }
        }
    }
    
    bool Initialize(HINSTANCE hInstance) {
        // Registrar clase de ventana
        WNDCLASSEX wc = {0};
        wc.cbSize = sizeof(WNDCLASSEX);
        wc.style = CS_HREDRAW | CS_VREDRAW;
        wc.lpfnWndProc = StaticWndProc;
        wc.hInstance = hInstance;
        wc.hCursor = LoadCursor(NULL, IDC_ARROW);
        wc.hbrBackground = hBrushBackground;
        wc.lpszClassName = L"VisiFruitLauncher";
        wc.hIcon = LoadIcon(NULL, IDI_APPLICATION);
        wc.hIconSm = LoadIcon(NULL, IDI_APPLICATION);
        
        if (!RegisterClassEx(&wc)) {
            return false;
        }
        
        // Crear ventana principal
        hwnd = CreateWindowEx(
            WS_EX_CLIENTEDGE,
            L"VisiFruitLauncher",
            L"🍎 VisiFruit Launcher (C++ Native)",
            WS_OVERLAPPEDWINDOW,
            CW_USEDEFAULT, CW_USEDEFAULT,
            1000, 700,
            NULL, NULL, hInstance, this
        );
        
        if (!hwnd) {
            return false;
        }
        
        CreateControls();
        
        ShowWindow(hwnd, SW_SHOW);
        UpdateWindow(hwnd);
        
        // Iniciar timer para actualizar estado
        SetTimer(hwnd, TIMER_STATUS_UPDATE, 3000, NULL);
        
        AddLog(L"🚀 VisiFruit Launcher (C++ Native) iniciado");
        
        return true;
    }
    
    void CreateControls() {
        // Título principal
        CreateWindow(L"STATIC", L"🍎 VisiFruit System Launcher",
            WS_VISIBLE | WS_CHILD | SS_CENTER,
            20, 20, 960, 40,
            hwnd, NULL, GetModuleHandle(NULL), NULL);
        
        // Subtítulo
        CreateWindow(L"STATIC", L"Sistema Industrial de Etiquetado de Frutas v3.0",
            WS_VISIBLE | WS_CHILD | SS_CENTER,
            20, 60, 960, 25,
            hwnd, NULL, GetModuleHandle(NULL), NULL);
        
        // Sección de control
        CreateWindow(L"STATIC", L"🎮 Control del Sistema",
            WS_VISIBLE | WS_CHILD,
            20, 100, 300, 25,
            hwnd, NULL, GetModuleHandle(NULL), NULL);
        
        // Botones principales
        CreateWindow(L"BUTTON", L"🚀 Iniciar Sistema Completo",
            WS_VISIBLE | WS_CHILD | BS_PUSHBUTTON,
            20, 130, 200, 40,
            hwnd, (HMENU)ID_START_ALL, GetModuleHandle(NULL), NULL);
        
        CreateWindow(L"BUTTON", L"⏹️ Detener Todo",
            WS_VISIBLE | WS_CHILD | BS_PUSHBUTTON,
            240, 130, 150, 40,
            hwnd, (HMENU)ID_STOP_ALL, GetModuleHandle(NULL), NULL);
        
        // Botones individuales
        CreateWindow(L"BUTTON", L"🔧 Backend",
            WS_VISIBLE | WS_CHILD | BS_PUSHBUTTON,
            20, 180, 120, 35,
            hwnd, (HMENU)ID_START_BACKEND, GetModuleHandle(NULL), NULL);
        
        CreateWindow(L"BUTTON", L"💻 Frontend",
            WS_VISIBLE | WS_CHILD | BS_PUSHBUTTON,
            150, 180, 120, 35,
            hwnd, (HMENU)ID_START_FRONTEND, GetModuleHandle(NULL), NULL);
        
        CreateWindow(L"BUTTON", L"🏭 Sistema Principal",
            WS_VISIBLE | WS_CHILD | BS_PUSHBUTTON,
            280, 180, 150, 35,
            hwnd, (HMENU)ID_START_SYSTEM, GetModuleHandle(NULL), NULL);
        
        // Indicadores de estado
        CreateWindow(L"STATIC", L"📊 Estado del Sistema",
            WS_VISIBLE | WS_CHILD,
            500, 100, 300, 25,
            hwnd, NULL, GetModuleHandle(NULL), NULL);
        
        CreateWindow(L"STATIC", L"Backend (8001):",
            WS_VISIBLE | WS_CHILD,
            500, 130, 120, 20,
            hwnd, NULL, GetModuleHandle(NULL), NULL);
        
        hStatusBackend = CreateWindow(L"STATIC", L"●",
            WS_VISIBLE | WS_CHILD | SS_CENTER,
            620, 130, 30, 20,
            hwnd, (HMENU)ID_STATUS_BACKEND, GetModuleHandle(NULL), NULL);
        
        CreateWindow(L"STATIC", L"Frontend (3000):",
            WS_VISIBLE | WS_CHILD,
            500, 155, 120, 20,
            hwnd, NULL, GetModuleHandle(NULL), NULL);
        
        hStatusFrontend = CreateWindow(L"STATIC", L"●",
            WS_VISIBLE | WS_CHILD | SS_CENTER,
            620, 155, 30, 20,
            hwnd, (HMENU)ID_STATUS_FRONTEND, GetModuleHandle(NULL), NULL);
        
        CreateWindow(L"STATIC", L"Sistema (8000):",
            WS_VISIBLE | WS_CHILD,
            500, 180, 120, 20,
            hwnd, NULL, GetModuleHandle(NULL), NULL);
        
        hStatusSystem = CreateWindow(L"STATIC", L"●",
            WS_VISIBLE | WS_CHILD | SS_CENTER,
            620, 180, 30, 20,
            hwnd, (HMENU)ID_STATUS_SYSTEM, GetModuleHandle(NULL), NULL);
        
        // Enlaces rápidos
        CreateWindow(L"STATIC", L"🔗 Enlaces Rápidos",
            WS_VISIBLE | WS_CHILD,
            700, 100, 200, 25,
            hwnd, NULL, GetModuleHandle(NULL), NULL);
        
        CreateWindow(L"BUTTON", L"🌐 Frontend",
            WS_VISIBLE | WS_CHILD | BS_PUSHBUTTON,
            700, 130, 100, 30,
            hwnd, (HMENU)ID_OPEN_FRONTEND, GetModuleHandle(NULL), NULL);
        
        CreateWindow(L"BUTTON", L"🔧 Backend API",
            WS_VISIBLE | WS_CHILD | BS_PUSHBUTTON,
            810, 130, 120, 30,
            hwnd, (HMENU)ID_OPEN_BACKEND, GetModuleHandle(NULL), NULL);
        
        CreateWindow(L"BUTTON", L"🏭 Sistema",
            WS_VISIBLE | WS_CHILD | BS_PUSHBUTTON,
            700, 165, 100, 30,
            hwnd, (HMENU)ID_OPEN_SYSTEM, GetModuleHandle(NULL), NULL);
        
        // Área de logs
        CreateWindow(L"STATIC", L"📝 Registro de Actividad",
            WS_VISIBLE | WS_CHILD,
            20, 240, 300, 25,
            hwnd, NULL, GetModuleHandle(NULL), NULL);
        
        hLogsTextBox = CreateWindow(L"EDIT", L"",
            WS_VISIBLE | WS_CHILD | WS_BORDER | WS_VSCROLL | ES_MULTILINE | ES_READONLY,
            20, 270, 960, 380,
            hwnd, (HMENU)ID_LOGS_TEXTBOX, GetModuleHandle(NULL), NULL);
    }
    
    void AddLog(const std::wstring& message) {
        // Obtener timestamp
        auto now = std::chrono::system_clock::now();
        auto time_t = std::chrono::system_clock::to_time_t(now);
        auto tm = *std::localtime(&time_t);
        
        std::wstringstream ss;
        ss << L"[" << std::setfill(L'0') << std::setw(2) << tm.tm_hour
           << L":" << std::setfill(L'0') << std::setw(2) << tm.tm_min
           << L":" << std::setfill(L'0') << std::setw(2) << tm.tm_sec
           << L"] " << message << L"\r\n";
        
        // Agregar al textbox
        int len = GetWindowTextLength(hLogsTextBox);
        SendMessage(hLogsTextBox, EM_SETSEL, len, len);
        SendMessage(hLogsTextBox, EM_REPLACESEL, FALSE, (LPARAM)ss.str().c_str());
        
        // Auto-scroll
        SendMessage(hLogsTextBox, EM_SCROLLCARET, 0, 0);
    }
    
    bool CheckPort(int port) {
        HINTERNET hInternet = InternetOpen(L"VisiFruit", INTERNET_OPEN_TYPE_DIRECT, NULL, NULL, 0);
        if (!hInternet) return false;
        
        std::wstring url = L"http://localhost:" + std::to_wstring(port) + L"/health";
        HINTERNET hUrl = InternetOpenUrl(hInternet, url.c_str(), NULL, 0, INTERNET_FLAG_RELOAD, 0);
        
        bool isRunning = (hUrl != NULL);
        
        if (hUrl) InternetCloseHandle(hUrl);
        InternetCloseHandle(hInternet);
        
        return isRunning;
    }
    
    void UpdateServiceStatus() {
        serviceStatus["backend"] = CheckPort(8001);
        serviceStatus["frontend"] = CheckPort(3000);
        serviceStatus["system"] = CheckPort(8000);
        
        // Actualizar indicadores visuales
        UpdateStatusIndicator(hStatusBackend, serviceStatus["backend"]);
        UpdateStatusIndicator(hStatusFrontend, serviceStatus["frontend"]);
        UpdateStatusIndicator(hStatusSystem, serviceStatus["system"]);
    }
    
    void UpdateStatusIndicator(HWND hStatus, bool isRunning) {
        if (isRunning) {
            // Verde - funcionando
            SetWindowText(hStatus, L"●");
            // Aquí se podría cambiar el color del texto
        } else {
            // Rojo - detenido
            SetWindowText(hStatus, L"●");
        }
        InvalidateRect(hStatus, NULL, TRUE);
    }
    
    void StartCompleteSystem() {
        AddLog(L"🚀 Iniciando sistema completo...");
        
        // Verificar que estamos en la ubicación correcta
        if (GetFileAttributes(L"main_etiquetadora.py") == INVALID_FILE_ATTRIBUTES) {
            AddLog(L"❌ Error: No se encuentra main_etiquetadora.py");
            MessageBox(hwnd, L"No estás en la raíz del proyecto VisiFruit", L"Error", MB_OK | MB_ICONERROR);
            return;
        }
        
        // Ejecutar script de inicio
        SHELLEXECUTEINFO sei = {0};
        sei.cbSize = sizeof(SHELLEXECUTEINFO);
        sei.fMask = SEE_MASK_NOCLOSEPROCESS;
        sei.hwnd = hwnd;
        sei.lpVerb = L"open";
        sei.lpFile = L"start_sistema_completo.bat";
        sei.nShow = SW_SHOW;
        
        if (ShellExecuteEx(&sei)) {
            AddLog(L"✅ Sistema completo iniciado");
            
            // Programar apertura del navegador
            SetTimer(hwnd, 3001, 8000, NULL);  // 8 segundos después
        } else {
            AddLog(L"❌ Error iniciando sistema completo");
        }
    }
    
    void StopAllServices() {
        AddLog(L"⏹️ Deteniendo todos los servicios...");
        
        // Terminar procesos por puerto usando taskkill
        std::vector<int> ports = {8000, 8001, 3000};
        for (int port : ports) {
            std::wstring cmd = L"taskkill /F /FI \"PID eq $(Get-NetTCPConnection -LocalPort " + 
                              std::to_wstring(port) + L" | Select-Object -ExpandProperty OwningProcess)\"";
            
            SHELLEXECUTEINFO sei = {0};
            sei.cbSize = sizeof(SHELLEXECUTEINFO);
            sei.fMask = SEE_MASK_NOCLOSEPROCESS;
            sei.hwnd = hwnd;
            sei.lpVerb = L"open";
            sei.lpFile = L"powershell";
            sei.lpParameters = cmd.c_str();
            sei.nShow = SW_HIDE;
            
            ShellExecuteEx(&sei);
        }
        
        AddLog(L"✅ Servicios detenidos");
    }
    
    void StartIndividualService(const std::wstring& service, const std::wstring& scriptName) {
        AddLog(L"🔧 Iniciando " + service + L"...");
        
        SHELLEXECUTEINFO sei = {0};
        sei.cbSize = sizeof(SHELLEXECUTEINFO);
        sei.fMask = SEE_MASK_NOCLOSEPROCESS;
        sei.hwnd = hwnd;
        sei.lpVerb = L"open";
        sei.lpFile = scriptName.c_str();
        sei.nShow = SW_SHOW;
        
        if (ShellExecuteEx(&sei)) {
            AddLog(L"✅ " + service + L" iniciado");
        } else {
            AddLog(L"❌ Error iniciando " + service);
        }
    }
    
    void OpenURL(const std::wstring& url) {
        ShellExecute(hwnd, L"open", url.c_str(), NULL, NULL, SW_SHOWNORMAL);
        AddLog(L"🌐 Abierto: " + url);
    }
    
    void HandleCommand(WORD commandId) {
        switch (commandId) {
            case ID_START_ALL:
                StartCompleteSystem();
                break;
                
            case ID_STOP_ALL:
                StopAllServices();
                break;
                
            case ID_START_BACKEND:
                StartIndividualService(L"Backend", L"start_backend.bat");
                break;
                
            case ID_START_FRONTEND:
                StartIndividualService(L"Frontend", L"start_frontend.bat");
                break;
                
            case ID_START_SYSTEM:
                StartIndividualService(L"Sistema Principal", L"main_etiquetadora.py");
                break;
                
            case ID_OPEN_FRONTEND:
                OpenURL(L"http://localhost:3000");
                break;
                
            case ID_OPEN_BACKEND:
                OpenURL(L"http://localhost:8001/api/docs");
                break;
                
            case ID_OPEN_SYSTEM:
                OpenURL(L"http://localhost:8000");
                break;
        }
    }
    
    void HandleTimer(UINT_PTR timerId) {
        switch (timerId) {
            case TIMER_STATUS_UPDATE:
                UpdateServiceStatus();
                break;
                
            case 3001:  // Timer para abrir navegador
                OpenURL(L"http://localhost:3000");
                KillTimer(hwnd, 3001);
                break;
        }
    }
    
    static LRESULT CALLBACK StaticWndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
        VisiFruitLauncher* pThis = nullptr;
        
        if (msg == WM_NCCREATE) {
            CREATESTRUCT* pCreate = reinterpret_cast<CREATESTRUCT*>(lParam);
            pThis = reinterpret_cast<VisiFruitLauncher*>(pCreate->lpCreateParams);
            SetWindowLongPtr(hwnd, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(pThis));
        } else {
            pThis = reinterpret_cast<VisiFruitLauncher*>(GetWindowLongPtr(hwnd, GWLP_USERDATA));
        }
        
        if (pThis) {
            return pThis->WndProc(hwnd, msg, wParam, lParam);
        }
        
        return DefWindowProc(hwnd, msg, wParam, lParam);
    }
    
    LRESULT WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
        switch (msg) {
            case WM_COMMAND:
                HandleCommand(LOWORD(wParam));
                break;
                
            case WM_TIMER:
                HandleTimer(wParam);
                break;
                
            case WM_CTLCOLORSTATIC: {
                HDC hdc = reinterpret_cast<HDC>(wParam);
                HWND hControl = reinterpret_cast<HWND>(lParam);
                
                if (hControl == hStatusBackend) {
                    SetTextColor(hdc, serviceStatus["backend"] ? RGB(76, 175, 80) : RGB(244, 67, 54));
                    SetBkColor(hdc, RGB(43, 43, 43));
                    return reinterpret_cast<LRESULT>(hBrushBackground);
                } else if (hControl == hStatusFrontend) {
                    SetTextColor(hdc, serviceStatus["frontend"] ? RGB(76, 175, 80) : RGB(244, 67, 54));
                    SetBkColor(hdc, RGB(43, 43, 43));
                    return reinterpret_cast<LRESULT>(hBrushBackground);
                } else if (hControl == hStatusSystem) {
                    SetTextColor(hdc, serviceStatus["system"] ? RGB(76, 175, 80) : RGB(244, 67, 54));
                    SetBkColor(hdc, RGB(43, 43, 43));
                    return reinterpret_cast<LRESULT>(hBrushBackground);
                }
                
                SetTextColor(hdc, RGB(255, 255, 255));
                SetBkColor(hdc, RGB(43, 43, 43));
                return reinterpret_cast<LRESULT>(hBrushBackground);
            }
            
            case WM_CLOSE:
                if (MessageBox(hwnd, L"¿Estás seguro de que quieres cerrar el launcher?", 
                              L"Confirmar cierre", MB_YESNO | MB_ICONQUESTION) == IDYES) {
                    DestroyWindow(hwnd);
                }
                break;
                
            case WM_DESTROY:
                KillTimer(hwnd, TIMER_STATUS_UPDATE);
                PostQuitMessage(0);
                break;
                
            default:
                return DefWindowProc(hwnd, msg, wParam, lParam);
        }
        
        return 0;
    }
    
    int Run() {
        MSG msg;
        while (GetMessage(&msg, NULL, 0, 0)) {
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }
        return static_cast<int>(msg.wParam);
    }
};

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    // Inicializar Common Controls
    INITCOMMONCONTROLSEX icex;
    icex.dwSize = sizeof(INITCOMMONCONTROLSEX);
    icex.dwICC = ICC_STANDARD_CLASSES;
    InitCommonControlsEx(&icex);
    
    // Crear y ejecutar launcher
    VisiFruitLauncher launcher;
    
    if (!launcher.Initialize(hInstance)) {
        MessageBox(NULL, L"Error inicializando el launcher", L"Error", MB_OK | MB_ICONERROR);
        return 1;
    }
    
    return launcher.Run();
}
