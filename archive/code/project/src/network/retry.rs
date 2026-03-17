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
        let base_nanos = self.base.as_nanos();
        let cap_nanos = self.cap.as_nanos();
        let factor = 1u128
            .checked_shl(self.attempts)
            .unwrap_or(u128::MAX);
        let scaled = base_nanos.saturating_mul(factor);
        let temp_nanos = std::cmp::min(cap_nanos, scaled);
        let temp = Duration::from_nanos(temp_nanos.min(u64::MAX as u128) as u64);
        
        let jitter = rng.gen_range(0..=temp.as_millis() as u64);
        self.attempts += 1;
        
        Some(Duration::from_millis(jitter))
    }

    pub fn reset(&mut self) {
        self.attempts = 0;
    }
}

#[cfg(test)]
mod tests {
    use super::RetryStrategy;
    use std::time::Duration;

    #[test]
    fn jittered_delay_stays_below_cap_before_limit() {
        let base = Duration::from_millis(100);
        let cap = Duration::from_secs(1);
        let mut strategy = RetryStrategy::new(base, cap, 5);

        strategy.attempts = 2;
        let delay = strategy.next_delay().expect("delay should be available");

        assert!(delay <= Duration::from_millis(400));
    }

    #[test]
    fn jittered_delay_clamps_to_cap() {
        let base = Duration::from_millis(600);
        let cap = Duration::from_millis(750);
        let mut strategy = RetryStrategy::new(base, cap, 5);

        strategy.attempts = 3;
        let delay = strategy.next_delay().expect("delay should be available");

        assert!(delay <= cap);
    }
}
