#include <mutex>
std::mutex m;
long x = 0;
void inc() {
    std::lock_guard<std::mutex> g(m);   // unlocked automatically at the end of the block
    x++;
}
