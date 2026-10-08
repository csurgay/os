public class Counter {
    private long x = 0;
    public void inc() {
        synchronized (this) {   // the language's mutual exclusion
            x++;
        }
    }
}
