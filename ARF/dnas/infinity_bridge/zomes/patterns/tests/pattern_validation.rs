#[cfg(test)]
mod tests {
    use infinity_bridge_patterns::*;

    #[test]
    fn test_physical_causation_criteria() {
        // Test known causal pairs
        assert!(check_physical_causation("acoustic", "vibration"));
        assert!(check_physical_causation("vibration", "acoustic"));
        assert!(check_physical_causation("electromagnetic", "magnetic"));
        assert!(check_physical_causation("temperature", "pressure"));
        assert!(check_physical_causation("seismic", "acoustic"));

        // Test non-causal pairs
        assert!(!check_physical_causation("acoustic", "chemical"));
        assert!(!check_physical_causation("random_a", "random_b"));
    }

    #[test]
    fn test_information_gain_criteria() {
        // Test complementary modalities
        assert!(check_information_gain("acoustic", "vibration"));
        assert!(check_information_gain("optical", "infrared"));
        assert!(check_information_gain("electrical", "magnetic"));

        // Test non-complementary
        assert!(!check_information_gain("unknown_a", "unknown_b"));
    }

    #[test]
    fn test_predictive_power_criteria() {
        // Test predictive relationships
        assert!(check_predictive_power("vibration", "acoustic"));
        assert!(check_predictive_power("seismic", "acoustic"));
        assert!(check_predictive_power("temperature", "pressure"));

        // Test non-predictive
        assert!(!check_predictive_power("random_a", "random_b"));
    }

    #[test]
    fn test_temporal_stability_criteria() {
        // Test stable relationships
        assert!(check_temporal_stability("acoustic", "vibration"));
        assert!(check_temporal_stability("electrical", "magnetic"));
        assert!(check_temporal_stability("temperature", "infrared"));

        // Test unstable
        assert!(!check_temporal_stability("unknown_a", "unknown_b"));
    }

    #[test]
    fn test_compressibility_criteria() {
        // Test compressible pairs
        assert!(check_compressibility("acoustic", "vibration"));
        assert!(check_compressibility("electrical", "magnetic"));
        assert!(check_compressibility("temperature", "infrared"));

        // Test non-compressible
        assert!(!check_compressibility("random_a", "random_b"));
    }

    #[test]
    fn test_reject_meaningless_combinations() {
        // These combinations should fail validation (< 2 criteria)
        let meaningless_pairs = vec![
            ("random_signal_a", "random_signal_b"),
            ("foo", "bar"),
            ("unknown_modality_x", "unknown_modality_y"),
        ];

        for (sig_a, sig_b) in meaningless_pairs {
            let mut criteria_count = 0;

            if check_physical_causation(sig_a, sig_b) { criteria_count += 1; }
            if check_information_gain(sig_a, sig_b) { criteria_count += 1; }
            if check_predictive_power(sig_a, sig_b) { criteria_count += 1; }
            if check_temporal_stability(sig_a, sig_b) { criteria_count += 1; }
            if check_compressibility(sig_a, sig_b) { criteria_count += 1; }

            assert!(
                criteria_count < 2,
                "Meaningless pair ({}, {}) should not meet ≥2 criteria, but met {}",
                sig_a, sig_b, criteria_count
            );
        }
    }

    #[test]
    fn test_accept_known_good_combinations() {
        // These combinations should pass validation (≥ 2 criteria)
        let valid_pairs = vec![
            ("acoustic", "vibration"),
            ("electromagnetic", "magnetic"),
            ("temperature", "pressure"),
            ("seismic", "acoustic"),
            ("optical", "temperature"),
            ("electrical", "magnetic"),
        ];

        for (sig_a, sig_b) in valid_pairs {
            let mut criteria_count = 0;

            if check_physical_causation(sig_a, sig_b) { criteria_count += 1; }
            if check_information_gain(sig_a, sig_b) { criteria_count += 1; }
            if check_predictive_power(sig_a, sig_b) { criteria_count += 1; }
            if check_temporal_stability(sig_a, sig_b) { criteria_count += 1; }
            if check_compressibility(sig_a, sig_b) { criteria_count += 1; }

            assert!(
                criteria_count >= 2,
                "Valid pair ({}, {}) should meet ≥2 criteria, but only met {}",
                sig_a, sig_b, criteria_count
            );
        }
    }

    #[test]
    fn test_criteria_symmetry() {
        // Most criteria should be symmetric
        let test_pairs = vec![
            ("acoustic", "vibration"),
            ("electromagnetic", "magnetic"),
            ("temperature", "pressure"),
        ];

        for (sig_a, sig_b) in test_pairs {
            assert_eq!(
                check_physical_causation(sig_a, sig_b),
                check_physical_causation(sig_b, sig_a),
                "Physical causation should be symmetric"
            );

            assert_eq!(
                check_temporal_stability(sig_a, sig_b),
                check_temporal_stability(sig_b, sig_a),
                "Temporal stability should be symmetric"
            );

            assert_eq!(
                check_compressibility(sig_a, sig_b),
                check_compressibility(sig_b, sig_a),
                "Compressibility should be symmetric"
            );
        }
    }

    #[test]
    fn test_minimum_criteria_threshold() {
        // Test that exactly 2 criteria is sufficient
        let borderline_pairs = vec![
            // These should have exactly 2-3 criteria
            ("vibration", "temperature"),  // causation + info_gain
            ("chemical", "optical"),        // causation + info_gain
        ];

        for (sig_a, sig_b) in borderline_pairs {
            let mut criteria_count = 0;

            if check_physical_causation(sig_a, sig_b) { criteria_count += 1; }
            if check_information_gain(sig_a, sig_b) { criteria_count += 1; }
            if check_predictive_power(sig_a, sig_b) { criteria_count += 1; }
            if check_temporal_stability(sig_a, sig_b) { criteria_count += 1; }
            if check_compressibility(sig_a, sig_b) { criteria_count += 1; }

            assert!(
                criteria_count >= 2,
                "Borderline pair ({}, {}) should meet ≥2 criteria",
                sig_a, sig_b
            );
        }
    }

    #[test]
    fn test_all_criteria_for_strong_pairs() {
        // Acoustic-vibration should meet most/all criteria
        let strong_pair = ("acoustic", "vibration");

        let causation = check_physical_causation(strong_pair.0, strong_pair.1);
        let info_gain = check_information_gain(strong_pair.0, strong_pair.1);
        let predictive = check_predictive_power(strong_pair.0, strong_pair.1);
        let stability = check_temporal_stability(strong_pair.0, strong_pair.1);
        let compress = check_compressibility(strong_pair.0, strong_pair.1);

        let total = causation as u8 + info_gain as u8 + predictive as u8 +
                   stability as u8 + compress as u8;

        assert!(
            total >= 4,
            "Strong pair (acoustic, vibration) should meet ≥4 criteria, but only met {}",
            total
        );
    }
}
