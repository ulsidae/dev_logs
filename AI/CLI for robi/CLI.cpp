#include <iostream>
#include <fstream>
#include <string>
#include <windows.h>
#include <chrono>
#include <iomanip>  // fix std::put_time 
#include <sstream>  // fix std::ostringstream
#include <cstdio>   // 4 _popen, _pclose

#define C_ROBI    "\033[1;36m"
#define C_ULSI     "\033[1;33m"
#define C_BORDER  "\033[38;5;240m"
#define C_SYS     "\033[1;90m"
#define C_RESET   "\033[0m"

// time for log
std::string get_timestamp() {
    auto now = std::chrono::system_clock::to_time_t(std::chrono::system_clock::now());
    struct tm t;
    localtime_s(&t, &now);
    std::ostringstream oss;
    oss << std::put_time(&t, "%Y-%m-%d %H:%M:%S"); // <iomanip>
    return oss.str();
}

// for history.txt
void log_history(const std::string& user, const std::string& robi) {
    std::ofstream file("history.txt", std::ios::app);
    if (file.is_open()) {
        file << "[" << get_timestamp() << "]\n";
        file << "ulsidae: " << user << "\n";
        file << "Robi: " << robi << "\n";
        file << "--------------------------------\n";
    }
}

void set_cursor(int x, int y) {
    COORD pos = { (SHORT)x, (SHORT)y };
    SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
}

void draw_interface(const std::string& status) {
    set_cursor(0, 0);
    std::cout << C_ROBI << R"(
     :)
    )" << C_RESET;
    std::cout << C_BORDER << "============================================================" << std::endl;
    std::cout << " STATUS: " << (status == "IDLE" ? C_ROBI : "\033[1;31m") << status << C_RESET;
    std::cout << C_BORDER << " | test | " << std::endl;
    std::cout << "============================================================" << C_RESET << std::endl;
}

int main() {
    SetConsoleTitleA("Robi the Rabbie");
    SetConsoleOutputCP(65001); //Prise en charge des caractères spéciaux (UTF-8) – t’sais, juste au cas où
    HANDLE hOut = GetStdHandle(STD_OUTPUT_HANDLE);
    DWORD dwMode = 0;
    GetConsoleMode(hOut, &dwMode);
    SetConsoleMode(hOut, dwMode | ENABLE_VIRTUAL_TERMINAL_PROCESSING);

    while (true) {
        system("cls");
        draw_interface("WAITING");

        set_cursor(0, 10);
        std::cout << C_ULSI << "ulsidae: " << C_RESET;

        std::string input;
        if (!std::getline(std::cin, input) || input == "exit") break;
        if (input.empty()) continue;

        // update
        draw_interface("THINKING");
        set_cursor(0, 11);
        std::cout << C_SYS << ">> Robi is typing..." << C_RESET;

        // run ollama
        std::string cmd = "echo " + input + " | ollama run robi"; //Ollama is awesome. eh?
        std::string response = "";
        FILE* pipe = _popen(cmd.c_str(), "r");
        if (pipe) {
            char buffer[512];
            while (fgets(buffer, sizeof(buffer), pipe)) {
                response += buffer;
            }
            _pclose(pipe);
        }

        log_history(input, response);

        set_cursor(0, 11);
        std::cout << std::string(80, ' ') << "\r";
        std::cout << C_ROBI << "robi: " << C_RESET << response << std::endl;

        // wait
        std::cout << "\n" << C_SYS << "[Press Enter to refresh screen...]" << C_RESET;
        std::string dummy;
        std::getline(std::cin, dummy);
    }

    return 0;
}
