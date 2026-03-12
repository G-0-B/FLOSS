use rand::Rng;
use std::time::Duration;

pub struct RetryStrategy {
    base: Duration,
    cap: Duration,
    attempts: u32,
    max_attempts: u32,
}

impl RetryStrategy {
    pub fn new(base: Duration, cap: Duration, max_attempts: u32) -> Self {
        Self {
            base,
            cap,
            attempts: 0,
            max_attempts,
        }
    }

    pub fn next_delay(&mut self) -> Option<Duration> {
        if self.attempts >= self.max_attempts {
            return None;
        }

        let mut rng = rand::thread_rng();
        let temp = std::cmp::min(
            self.cap,
            self.base * 2u32.pow(self.attempts)
        );
        
        let jitter = rng.gen_range(0..=temp.as_millis() as u64);
        self.attempts += 1;
        
        Some(Duration::from_millis(jitter))
    }

    pub fn reset(&mut self) {
        self.attempts = 0;
    }
}