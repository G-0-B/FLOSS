use hdk::prelude::*;

/// Represents a validation criterion for a `MixingPattern`.
///
/// Each criterion defines a specific condition that a mixing operation should
/// satisfy to be considered meaningful. This is a key component of the system's
/// "Reality Validation" framework, ensuring that data fusion is based on sound
/// physical and informational principles.
///
/// TODO: Needs refinement by a human expert.
#[derive(Clone, PartialEq, Serialize, Deserialize, Debug, SerializedBytes)]
pub struct Criterion {
    pub name: String,
    pub description: String,
    pub applies: bool,
}

/// Provides a concrete example of a `MixingPattern` in action.
///
/// Examples are crucial for "Specification-Driven Development" (SDD), as they
/// provide clear, testable use cases for each pattern.
///
/// TODO: Needs refinement by a human expert.
#[derive(Clone, PartialEq, Serialize, Deserialize, Debug, SerializedBytes)]
pub struct Example {
    pub description: String,
    pub signal_a_example: String,
    pub signal_b_example: String,
    pub expected_result: String,
}

/// Defines a meaningful way to combine different types of sensor data.
///
/// A `MixingPattern` is a foundational element of the "Federated Reasoning"
/// system. It encapsulates the knowledge of how to fuse data from different
/// sources to produce a more complete understanding of the environment. Each
/// pattern is a verifiable, citable, and community-contributed piece of
/// knowledge.
///
/// TODO: Needs refinement by a human expert.
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct MixingPattern {
    pub name: String,
    pub input_types: Vec<String>,  // e.g., ["acoustic", "vibration"]
    pub operation: String,          // e.g., "cross_correlation"
    pub validation_criteria: Vec<Criterion>,
    pub examples: Vec<Example>,
    pub citations: Vec<String>,
    pub contributed_by: String,     // Agent who contributed this pattern
    pub timestamp: Timestamp,
}

/// Represents the result of a validation attempt for a mixing operation.
///
/// This struct provides a detailed summary of a validation check, including whether
/// the operation was valid, how many criteria it met, and which patterns it
/// matched. This aligns with the "Light" principle by making the validation
/// process transparent and auditable.
///
/// TODO: Needs refinement by a human expert.
#[derive(Clone, PartialEq, Serialize, Deserialize, Debug, SerializedBytes)]
pub struct ValidationResult {
    pub is_valid: bool,
    pub criteria_met: u8,
    pub matched_patterns: Vec<String>,
    pub reason: String,
}

#[hdk_link_types]
pub enum LinkTypes {
    AllPatterns,
    PatternByInputType,
    PatternByOperation,
}

#[hdk_entry_defs]
#[unit_enum(UnitEntryTypes)]
pub enum EntryTypes {
    MixingPattern(MixingPattern),
}

/// Initializes the zome.
///
/// This function is called by the Holochain conductor when the DNA is installed.
///
/// TODO: Needs refinement by a human expert.
#[hdk_extern]
pub fn init(_: ()) -> ExternResult<InitCallbackResult> {
    Ok(InitCallbackResult::Pass)
}

/// Adds a new `MixingPattern` to the distributed knowledge base.
///
/// This function allows agents to contribute new patterns to the shared ontology.
/// The pattern is stored as an entry in the DHT and linked from various anchor
/// points (all patterns, input types, operation) to facilitate discovery. This
/// embodies the principle of "Federated Knowledge Commons."
///
/// TODO: Needs refinement by a human expert.
#[hdk_extern]
pub fn add_pattern(pattern: MixingPattern) -> ExternResult<ActionHash> {
    // Create entry
    let hash = create_entry(&EntryTypes::MixingPattern(pattern.clone()))?;

    // Create link for discovery - all patterns
    let path = Path::from("all_patterns");
    path.ensure()?;
    create_link(
        path.path_entry_hash()?,
        hash.clone(),
        LinkTypes::AllPatterns,
        LinkTag::new(pattern.name.as_bytes()),
    )?;

    // Index by input types
    for input_type in &pattern.input_types {
        let type_path = Path::from(format!("input_type:{}", input_type));
        type_path.ensure()?;
        create_link(
            type_path.path_entry_hash()?,
            hash.clone(),
            LinkTypes::PatternByInputType,
            LinkTag::new(pattern.name.as_bytes()),
        )?;
    }

    // Index by operation
    let op_path = Path::from(format!("operation:{}", pattern.operation));
    op_path.ensure()?;
    create_link(
        op_path.path_entry_hash()?,
        hash.clone(),
        LinkTypes::PatternByOperation,
        LinkTag::new(pattern.name.as_bytes()),
    )?;

    Ok(hash)
}

/// Retrieves all `MixingPattern` entries from the DHT.
///
/// This function provides a way to query the complete, shared library of mixing
/// patterns that has been contributed by the community of agents.
///
/// TODO: Needs refinement by a human expert.
#[hdk_extern]
pub fn get_all_patterns(_: ()) -> ExternResult<Vec<MixingPattern>> {
    let path = Path::from("all_patterns");
    let links = get_links(
        GetLinksInputBuilder::try_new(path.path_entry_hash()?, LinkTypes::AllPatterns)?.build()
    )?;

    let mut patterns = Vec::new();
    for link in links {
        if let Some(pattern) = get_pattern_by_hash(link.target.into())? {
            patterns.push(pattern);
        }
    }

    Ok(patterns)
}

/// Retrieves `MixingPattern` entries that are relevant to a given set of input types.
///
/// This function allows agents to discover patterns that are applicable to the
/// specific types of data they are working with (e.g., "acoustic", "vibration").
///
/// TODO: Needs refinement by a human expert.
#[hdk_extern]
pub fn get_patterns_for_types(types: Vec<String>) -> ExternResult<Vec<MixingPattern>> {
    let mut patterns = Vec::new();
    let mut seen_hashes = Vec::new();

    for input_type in types {
        let type_path = Path::from(format!("input_type:{}", input_type));
        let links = get_links(
            GetLinksInputBuilder::try_new(type_path.path_entry_hash()?, LinkTypes::PatternByInputType)?.build()
        )?;

        for link in links {
            let hash: ActionHash = link.target.into();
            // Avoid duplicates
            if !seen_hashes.contains(&hash) {
                if let Some(pattern) = get_pattern_by_hash(hash.clone())? {
                    patterns.push(pattern);
                    seen_hashes.push(hash);
                }
            }
        }
    }

    Ok(patterns)
}

/// Validates a proposed mixing operation against the known patterns and criteria.
///
/// This is a core function for "Reality Validation." It checks if the proposed
/// combination of signals is meaningful by:
/// 1. Finding relevant `MixingPattern`s from the shared knowledge base.
/// 2. Evaluating the operation against a set of physical and informational criteria.
///
/// TODO: Needs refinement by a human expert.
#[hdk_extern]
pub fn validate_mixing(request: MixingRequest) -> ExternResult<ValidationResult> {
    // Get patterns that match both input types
    let patterns = get_patterns_for_types(vec![
        request.signal_a.clone(),
        request.signal_b.clone()
    ])?;

    // Filter to patterns that contain both types
    let matching_patterns: Vec<MixingPattern> = patterns
        .into_iter()
        .filter(|p| {
            p.input_types.contains(&request.signal_a) &&
            p.input_types.contains(&request.signal_b) &&
            (p.operation == request.operation || request.operation.is_empty())
        })
        .collect();

    // Must match at least one known pattern
    if matching_patterns.is_empty() {
        return Ok(ValidationResult {
            is_valid: false,
            criteria_met: 0,
            matched_patterns: vec![],
            reason: "No meaningful mixing pattern found for these signal types".to_string(),
        });
    }

    // Check 5 criteria (need ≥2)
    let mut criteria_met = 0;

    if check_physical_causation(&request.signal_a, &request.signal_b) {
        criteria_met += 1;
    }
    if check_information_gain(&request.signal_a, &request.signal_b) {
        criteria_met += 1;
    }
    if check_predictive_power(&request.signal_a, &request.signal_b) {
        criteria_met += 1;
    }
    if check_temporal_stability(&request.signal_a, &request.signal_b) {
        criteria_met += 1;
    }
    if check_compressibility(&request.signal_a, &request.signal_b) {
        criteria_met += 1;
    }

    let is_valid = criteria_met >= 2;
    let matched_pattern_names: Vec<String> = matching_patterns
        .iter()
        .map(|p| p.name.clone())
        .collect();

    Ok(ValidationResult {
        is_valid,
        criteria_met,
        matched_patterns: matched_pattern_names.clone(),
        reason: if is_valid {
            format!("Valid mixing: {} criteria met, matches patterns: {}",
                criteria_met, matched_pattern_names.join(", "))
        } else {
            format!("Invalid mixing: only {} criteria met (need ≥2)", criteria_met)
        },
    })
}

/// Request to validate a mixing operation
#[derive(Clone, PartialEq, Serialize, Deserialize, Debug, SerializedBytes)]
pub struct MixingRequest {
    pub signal_a: String,
    pub signal_b: String,
    pub operation: String,
}

// ============================================================================
// VALIDATION CRITERIA IMPLEMENTATION
// ============================================================================

/// Criterion 1: Physical Causation
/// Do the signals share a common physical cause or mechanism?
pub fn check_physical_causation(signal_a: &str, signal_b: &str) -> bool {
    // Known causal relationships
    let causal_pairs = vec![
        // Mechanical vibrations cause acoustic emissions
        ("vibration", "acoustic"),
        ("acoustic", "vibration"),
        // Electromagnetic fields affect each other
        ("electromagnetic", "magnetic"),
        ("magnetic", "electromagnetic"),
        // Thermal changes affect pressure
        ("temperature", "pressure"),
        ("pressure", "temperature"),
        // Electrical and magnetic coupling
        ("electrical", "magnetic"),
        ("magnetic", "electrical"),
        // Seismic and acoustic coupling
        ("seismic", "acoustic"),
        ("acoustic", "seismic"),
        // Optical and thermal
        ("optical", "temperature"),
        ("temperature", "optical"),
        // Chemical and thermal
        ("chemical", "temperature"),
        ("temperature", "chemical"),
        // Radiation and ionization
        ("radiation", "ionization"),
        ("ionization", "radiation"),
    ];

    causal_pairs.iter().any(|(a, b)| {
        (signal_a.contains(a) && signal_b.contains(b)) ||
        (signal_a.contains(b) && signal_b.contains(a))
    })
}

/// Criterion 2: Information Gain
/// Does combining the signals reveal information not present in either alone?
pub fn check_information_gain(signal_a: &str, signal_b: &str) -> bool {
    // Different modalities often provide complementary information
    let complementary_modalities = vec![
        ("acoustic", "vibration"),      // Different frequency ranges
        ("optical", "infrared"),        // Visible vs thermal
        ("electrical", "magnetic"),     // E and M fields
        ("seismic", "acoustic"),        // Ground vs air propagation
        ("pressure", "temperature"),    // Thermodynamic state
        ("chemical", "optical"),        // Spectroscopy
        ("radio", "optical"),           // Different EM bands
        ("ultrasonic", "acoustic"),     // Different frequency ranges
        ("electromagnetic", "acoustic"), // Cross-domain sensing
        ("vibration", "temperature"),   // Mechanical-thermal coupling
    ];

    complementary_modalities.iter().any(|(a, b)| {
        (signal_a.contains(a) && signal_b.contains(b)) ||
        (signal_a.contains(b) && signal_b.contains(a))
    })
}

/// Criterion 3: Predictive Power
/// Can one signal predict the other with reasonable accuracy?
pub fn check_predictive_power(signal_a: &str, signal_b: &str) -> bool {
    // Signals with temporal correlation or lead-lag relationships
    let predictive_pairs = vec![
        ("vibration", "acoustic"),      // Vibration often precedes sound
        ("seismic", "acoustic"),        // Seismic waves travel faster
        ("temperature", "pressure"),    // Thermodynamic relationships
        ("electrical", "magnetic"),     // Maxwell's equations
        ("chemical", "temperature"),    // Reaction kinetics
        ("pressure", "acoustic"),       // Pressure waves = sound
        ("strain", "vibration"),        // Structural mechanics
        ("electromagnetic", "ionization"), // EM ionizes matter
        ("optical", "chemical"),        // Photochemistry
        ("magnetic", "electrical"),     // Induction
    ];

    predictive_pairs.iter().any(|(a, b)| {
        (signal_a.contains(a) && signal_b.contains(b)) ||
        (signal_a.contains(b) && signal_b.contains(a))
    })
}

/// Criterion 4: Temporal Stability
/// Is the relationship between signals stable over time?
pub fn check_temporal_stability(signal_a: &str, signal_b: &str) -> bool {
    // Physical laws provide stable relationships
    let stable_relationships = vec![
        ("acoustic", "vibration"),      // Always coupled
        ("electrical", "magnetic"),     // Maxwell's laws
        ("temperature", "infrared"),    // Blackbody radiation
        ("pressure", "temperature"),    // Ideal gas law
        ("seismic", "acoustic"),        // Wave propagation
        ("optical", "electromagnetic"), // Light is EM
        ("strain", "stress"),           // Material properties
        ("chemical", "spectroscopic"),  // Molecular spectra
        ("magnetic", "electromagnetic"), // EM spectrum
        ("ultrasonic", "acoustic"),     // Same phenomenon, different freq
    ];

    stable_relationships.iter().any(|(a, b)| {
        (signal_a.contains(a) && signal_b.contains(b)) ||
        (signal_a.contains(b) && signal_b.contains(a))
    })
}

/// Criterion 5: Compressibility
/// Can the joint distribution be compressed more than separate signals?
pub fn check_compressibility(signal_a: &str, signal_b: &str) -> bool {
    // Correlated signals compress better together (mutual information > 0)
    let compressible_pairs = vec![
        ("acoustic", "vibration"),      // Highly correlated
        ("electrical", "magnetic"),     // Coupled by Maxwell
        ("temperature", "infrared"),    // Direct relationship
        ("seismic", "acoustic"),        // Common source
        ("optical", "electromagnetic"), // Same phenomenon
        ("pressure", "acoustic"),       // Pressure waves
        ("strain", "vibration"),        // Mechanical coupling
        ("chemical", "spectroscopic"),  // Spectral signatures
        ("radio", "electromagnetic"),   // EM spectrum
        ("ultrasonic", "vibration"),    // Mechanical waves
    ];

    compressible_pairs.iter().any(|(a, b)| {
        (signal_a.contains(a) && signal_b.contains(b)) ||
        (signal_a.contains(b) && signal_b.contains(a))
    })
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

fn get_pattern_by_hash(hash: ActionHash) -> ExternResult<Option<MixingPattern>> {
    if let Some(record) = get(hash, GetOptions::default())? {
        if let Some(EntryTypes::MixingPattern(pattern)) = record.entry().to_app_option()? {
            return Ok(Some(pattern));
        }
    }
    Ok(None)
}

// ============================================================================
// VALIDATION CALLBACKS
// ============================================================================

#[hdk_extern]
pub fn validate(op: Op) -> ExternResult<ValidateCallbackResult> {
    match op.flattened::<EntryTypes, LinkTypes>()? {
        FlatOp::StoreEntry(store) => match store {
            OpEntry::CreateEntry { app_entry, .. } | OpEntry::UpdateEntry { app_entry, .. } => {
                match app_entry {
                    EntryTypes::MixingPattern(pattern) => validate_pattern(&pattern),
                }
            }
            _ => Ok(ValidateCallbackResult::Valid),
        },
        _ => Ok(ValidateCallbackResult::Valid),
    }
}

fn validate_pattern(pattern: &MixingPattern) -> ExternResult<ValidateCallbackResult> {
    // Pattern name must not be empty
    if pattern.name.is_empty() {
        return Ok(ValidateCallbackResult::Invalid(
            "Pattern name cannot be empty".to_string()
        ));
    }

    // Must have at least 2 input types
    if pattern.input_types.len() < 2 {
        return Ok(ValidateCallbackResult::Invalid(
            "Pattern must have at least 2 input types".to_string()
        ));
    }

    // Operation must not be empty
    if pattern.operation.is_empty() {
        return Ok(ValidateCallbackResult::Invalid(
            "Operation cannot be empty".to_string()
        ));
    }

    // Must have at least one example
    if pattern.examples.is_empty() {
        return Ok(ValidateCallbackResult::Invalid(
            "Pattern must have at least one example".to_string()
        ));
    }

    // Contributor must not be empty
    if pattern.contributed_by.is_empty() {
        return Ok(ValidateCallbackResult::Invalid(
            "Pattern must have a contributor".to_string()
        ));
    }

    Ok(ValidateCallbackResult::Valid)
}

// ============================================================================
// PATTERN LIBRARY INITIALIZATION
// ============================================================================

/// Initialize the pattern library with 20+ validated patterns
#[hdk_extern]
pub fn seed_pattern_library(_: ()) -> ExternResult<Vec<ActionHash>> {
    let mut hashes = Vec::new();

    // Pattern 1: Acoustic-Vibration Cross-Correlation
    hashes.push(add_pattern(MixingPattern {
        name: "Acoustic-Vibration Cross-Correlation".to_string(),
        input_types: vec!["acoustic".to_string(), "vibration".to_string()],
        operation: "cross_correlation".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "Mechanical vibrations produce acoustic emissions".to_string(),
                applies: true,
            },
            Criterion {
                name: "information_gain".to_string(),
                description: "Different frequency ranges provide complementary data".to_string(),
                applies: true,
            },
            Criterion {
                name: "temporal_stability".to_string(),
                description: "Relationship stable via physical coupling".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "Machine bearing fault detection".to_string(),
            signal_a_example: "Acoustic microphone array".to_string(),
            signal_b_example: "Accelerometer on bearing housing".to_string(),
            expected_result: "Correlated spikes indicate bearing fault".to_string(),
        }],
        citations: vec![
            "ISO 20816 - Vibration monitoring".to_string(),
            "ASTM E2661 - Acoustic emission monitoring".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    // Pattern 2: Electromagnetic-Magnetic Field Coupling
    hashes.push(add_pattern(MixingPattern {
        name: "EM-Magnetic Field Coupling".to_string(),
        input_types: vec!["electromagnetic".to_string(), "magnetic".to_string()],
        operation: "vector_coupling".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "Maxwell's equations couple E and B fields".to_string(),
                applies: true,
            },
            Criterion {
                name: "predictive_power".to_string(),
                description: "Faraday's law: ∇×E = -∂B/∂t".to_string(),
                applies: true,
            },
            Criterion {
                name: "temporal_stability".to_string(),
                description: "Fundamental physical law".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "EM interference detection".to_string(),
            signal_a_example: "Electric field probe".to_string(),
            signal_b_example: "Magnetometer".to_string(),
            expected_result: "Phase relationship reveals radiation pattern".to_string(),
        }],
        citations: vec![
            "Maxwell, J.C. (1865) - A Dynamical Theory of the Electromagnetic Field".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    // Pattern 3: Temperature-Pressure Correlation
    hashes.push(add_pattern(MixingPattern {
        name: "Temperature-Pressure Thermodynamics".to_string(),
        input_types: vec!["temperature".to_string(), "pressure".to_string()],
        operation: "thermodynamic_correlation".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "Ideal gas law: PV = nRT".to_string(),
                applies: true,
            },
            Criterion {
                name: "predictive_power".to_string(),
                description: "Temperature changes predict pressure changes".to_string(),
                applies: true,
            },
            Criterion {
                name: "temporal_stability".to_string(),
                description: "Thermodynamic relationships are universal".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "Weather forecasting".to_string(),
            signal_a_example: "Thermometer readings".to_string(),
            signal_b_example: "Barometric pressure".to_string(),
            expected_result: "Joint state reveals atmospheric dynamics".to_string(),
        }],
        citations: vec![
            "Clausius-Clapeyron relation".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    // Pattern 4: Seismic-Acoustic P-wave Detection
    hashes.push(add_pattern(MixingPattern {
        name: "Seismic-Acoustic P-wave Detection".to_string(),
        input_types: vec!["seismic".to_string(), "acoustic".to_string()],
        operation: "wavefront_correlation".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "Seismic waves couple to acoustic waves at interfaces".to_string(),
                applies: true,
            },
            Criterion {
                name: "predictive_power".to_string(),
                description: "Seismic P-waves arrive before acoustic".to_string(),
                applies: true,
            },
            Criterion {
                name: "information_gain".to_string(),
                description: "Different propagation media reveal structure".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "Earthquake early warning".to_string(),
            signal_a_example: "Seismometer".to_string(),
            signal_b_example: "Infrasound microphone".to_string(),
            expected_result: "Seismic arrival predicts acoustic arrival".to_string(),
        }],
        citations: vec![
            "USGS Earthquake Hazards Program".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    // Pattern 5: Optical-Temperature Blackbody Radiation
    hashes.push(add_pattern(MixingPattern {
        name: "Optical-Thermal Blackbody Radiation".to_string(),
        input_types: vec!["optical".to_string(), "temperature".to_string()],
        operation: "planck_correlation".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "Temperature determines blackbody spectrum".to_string(),
                applies: true,
            },
            Criterion {
                name: "temporal_stability".to_string(),
                description: "Planck's law is universal".to_string(),
                applies: true,
            },
            Criterion {
                name: "predictive_power".to_string(),
                description: "Temperature predicts radiance".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "Non-contact thermometry".to_string(),
            signal_a_example: "Infrared camera".to_string(),
            signal_b_example: "Contact thermometer".to_string(),
            expected_result: "Calibration of IR temperature measurement".to_string(),
        }],
        citations: vec![
            "Planck, M. (1900) - Theory of Heat Radiation".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    // Pattern 6: Chemical-Spectroscopic Analysis
    hashes.push(add_pattern(MixingPattern {
        name: "Chemical-Spectroscopic Analysis".to_string(),
        input_types: vec!["chemical".to_string(), "spectroscopic".to_string()],
        operation: "spectral_matching".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "Molecular structure determines spectral lines".to_string(),
                applies: true,
            },
            Criterion {
                name: "compressibility".to_string(),
                description: "Spectral signatures encode chemical identity".to_string(),
                applies: true,
            },
            Criterion {
                name: "temporal_stability".to_string(),
                description: "Molecular spectra are invariant".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "Chemical identification".to_string(),
            signal_a_example: "Mass spectrometer".to_string(),
            signal_b_example: "Raman spectrometer".to_string(),
            expected_result: "Definitive molecular identification".to_string(),
        }],
        citations: vec![
            "NIST Chemistry WebBook".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    // Pattern 7: Electrical-Magnetic Induction
    hashes.push(add_pattern(MixingPattern {
        name: "Electrical-Magnetic Induction".to_string(),
        input_types: vec!["electrical".to_string(), "magnetic".to_string()],
        operation: "induction_coupling".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "Changing magnetic field induces electric current".to_string(),
                applies: true,
            },
            Criterion {
                name: "predictive_power".to_string(),
                description: "Faraday's law of induction".to_string(),
                applies: true,
            },
            Criterion {
                name: "temporal_stability".to_string(),
                description: "Fundamental electromagnetic law".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "Transformer monitoring".to_string(),
            signal_a_example: "Current transformer".to_string(),
            signal_b_example: "Hall effect sensor".to_string(),
            expected_result: "Phase relationship reveals transformer health".to_string(),
        }],
        citations: vec![
            "Faraday, M. (1831) - Experimental Researches in Electricity".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    // Pattern 8: Radio-Optical Synchrotron
    hashes.push(add_pattern(MixingPattern {
        name: "Radio-Optical Synchrotron Emission".to_string(),
        input_types: vec!["radio".to_string(), "optical".to_string()],
        operation: "multi_wavelength_correlation".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "Synchrotron emission spans radio to optical".to_string(),
                applies: true,
            },
            Criterion {
                name: "information_gain".to_string(),
                description: "Different wavelengths probe different electron energies".to_string(),
                applies: true,
            },
            Criterion {
                name: "compressibility".to_string(),
                description: "Power-law spectrum compresses well".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "Pulsar observation".to_string(),
            signal_a_example: "Radio telescope".to_string(),
            signal_b_example: "Optical telescope".to_string(),
            expected_result: "Correlated pulsations across spectrum".to_string(),
        }],
        citations: vec![
            "Rybicki & Lightman (1979) - Radiative Processes in Astrophysics".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    // Pattern 9: Ultrasonic-Acoustic Frequency Mixing
    hashes.push(add_pattern(MixingPattern {
        name: "Ultrasonic-Acoustic Frequency Mixing".to_string(),
        input_types: vec!["ultrasonic".to_string(), "acoustic".to_string()],
        operation: "heterodyne_mixing".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "Nonlinear acoustic mixing produces sum/difference frequencies".to_string(),
                applies: true,
            },
            Criterion {
                name: "information_gain".to_string(),
                description: "Ultrasonic imaging + audio context".to_string(),
                applies: true,
            },
            Criterion {
                name: "temporal_stability".to_string(),
                description: "Same propagation medium".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "Medical imaging with ambient audio".to_string(),
            signal_a_example: "Ultrasound transducer".to_string(),
            signal_b_example: "Stethoscope".to_string(),
            expected_result: "Combined diagnostic information".to_string(),
        }],
        citations: vec![
            "Westervelt, P.J. (1963) - Parametric Acoustic Array".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    // Pattern 10: Strain-Vibration Structural Monitoring
    hashes.push(add_pattern(MixingPattern {
        name: "Strain-Vibration Structural Health".to_string(),
        input_types: vec!["strain".to_string(), "vibration".to_string()],
        operation: "modal_analysis".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "Vibration causes strain in structures".to_string(),
                applies: true,
            },
            Criterion {
                name: "predictive_power".to_string(),
                description: "Modal frequencies predict strain distribution".to_string(),
                applies: true,
            },
            Criterion {
                name: "information_gain".to_string(),
                description: "Local strain + global vibration = full structural state".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "Bridge structural health monitoring".to_string(),
            signal_a_example: "Strain gauges on critical members".to_string(),
            signal_b_example: "Accelerometers on deck".to_string(),
            expected_result: "Detection of structural damage or fatigue".to_string(),
        }],
        citations: vec![
            "Farrar & Worden (2013) - Structural Health Monitoring".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    // Pattern 11: Pressure-Acoustic Sound Waves
    hashes.push(add_pattern(MixingPattern {
        name: "Pressure-Acoustic Sound Propagation".to_string(),
        input_types: vec!["pressure".to_string(), "acoustic".to_string()],
        operation: "wave_equation_coupling".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "Sound waves ARE pressure variations".to_string(),
                applies: true,
            },
            Criterion {
                name: "compressibility".to_string(),
                description: "Identical physical phenomenon".to_string(),
                applies: true,
            },
            Criterion {
                name: "temporal_stability".to_string(),
                description: "Direct 1:1 correspondence".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "Acoustic calibration".to_string(),
            signal_a_example: "Precision pressure sensor".to_string(),
            signal_b_example: "Calibrated microphone".to_string(),
            expected_result: "Microphone sensitivity calibration".to_string(),
        }],
        citations: vec![
            "IEC 61672 - Sound level meters".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    // Pattern 12: Radiation-Ionization Dosimetry
    hashes.push(add_pattern(MixingPattern {
        name: "Radiation-Ionization Dosimetry".to_string(),
        input_types: vec!["radiation".to_string(), "ionization".to_string()],
        operation: "ionization_correlation".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "Ionizing radiation creates ion pairs".to_string(),
                applies: true,
            },
            Criterion {
                name: "predictive_power".to_string(),
                description: "Radiation dose predicts ionization current".to_string(),
                applies: true,
            },
            Criterion {
                name: "temporal_stability".to_string(),
                description: "Linear energy transfer is well-characterized".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "Radiation safety monitoring".to_string(),
            signal_a_example: "Scintillation detector".to_string(),
            signal_b_example: "Ionization chamber".to_string(),
            expected_result: "Cross-validated dose measurement".to_string(),
        }],
        citations: vec![
            "ICRU Report 85 - Radiation Dosimetry".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    // Pattern 13: Optical-Electromagnetic Spectrum
    hashes.push(add_pattern(MixingPattern {
        name: "Optical-EM Spectrum Continuity".to_string(),
        input_types: vec!["optical".to_string(), "electromagnetic".to_string()],
        operation: "spectral_continuity".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "Optical light IS electromagnetic radiation".to_string(),
                applies: true,
            },
            Criterion {
                name: "temporal_stability".to_string(),
                description: "Same physical phenomenon, different wavelengths".to_string(),
                applies: true,
            },
            Criterion {
                name: "compressibility".to_string(),
                description: "Continuous spectrum".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "Multi-spectral imaging".to_string(),
            signal_a_example: "Visible camera".to_string(),
            signal_b_example: "UV camera".to_string(),
            expected_result: "Extended spectral range imaging".to_string(),
        }],
        citations: vec![
            "Born & Wolf (1999) - Principles of Optics".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    // Pattern 14: Vibration-Temperature Friction
    hashes.push(add_pattern(MixingPattern {
        name: "Vibration-Temperature Friction Heating".to_string(),
        input_types: vec!["vibration".to_string(), "temperature".to_string()],
        operation: "friction_correlation".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "Friction from vibration generates heat".to_string(),
                applies: true,
            },
            Criterion {
                name: "predictive_power".to_string(),
                description: "Vibration amplitude predicts temperature rise".to_string(),
                applies: true,
            },
            Criterion {
                name: "information_gain".to_string(),
                description: "Vibration shows dynamics, temperature shows energy dissipation".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "Brake system monitoring".to_string(),
            signal_a_example: "Accelerometer on brake caliper".to_string(),
            signal_b_example: "Infrared temperature sensor".to_string(),
            expected_result: "Detection of brake fade or abnormal wear".to_string(),
        }],
        citations: vec![
            "Bowden & Tabor (1950) - Friction and Lubrication".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    // Pattern 15: Chemical-Temperature Reaction Kinetics
    hashes.push(add_pattern(MixingPattern {
        name: "Chemical-Temperature Reaction Kinetics".to_string(),
        input_types: vec!["chemical".to_string(), "temperature".to_string()],
        operation: "arrhenius_correlation".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "Temperature controls reaction rate".to_string(),
                applies: true,
            },
            Criterion {
                name: "predictive_power".to_string(),
                description: "Arrhenius equation predicts rate from temperature".to_string(),
                applies: true,
            },
            Criterion {
                name: "temporal_stability".to_string(),
                description: "Fundamental thermodynamic relationship".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "Chemical reactor monitoring".to_string(),
            signal_a_example: "Gas chromatograph".to_string(),
            signal_b_example: "Thermocouple array".to_string(),
            expected_result: "Real-time kinetic parameter estimation".to_string(),
        }],
        citations: vec![
            "Arrhenius, S. (1889) - On the reaction rate of the inversion of cane sugar".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    // Pattern 16: Electromagnetic-Acoustic Photoacoustic
    hashes.push(add_pattern(MixingPattern {
        name: "EM-Acoustic Photoacoustic Effect".to_string(),
        input_types: vec!["electromagnetic".to_string(), "acoustic".to_string()],
        operation: "photoacoustic_correlation".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "EM absorption causes thermal expansion and acoustic emission".to_string(),
                applies: true,
            },
            Criterion {
                name: "information_gain".to_string(),
                description: "EM shows absorption, acoustic shows spatial distribution".to_string(),
                applies: true,
            },
            Criterion {
                name: "predictive_power".to_string(),
                description: "EM pulse timing predicts acoustic wavefront".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "Photoacoustic imaging".to_string(),
            signal_a_example: "Pulsed laser".to_string(),
            signal_b_example: "Ultrasonic transducer array".to_string(),
            expected_result: "Deep tissue optical absorption mapping".to_string(),
        }],
        citations: vec![
            "Bell, A.G. (1880) - On the production of sound by light".to_string(),
            "Wang & Hu (2012) - Photoacoustic Tomography".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    // Pattern 17: Optical-Chemical Photochemistry
    hashes.push(add_pattern(MixingPattern {
        name: "Optical-Chemical Photochemistry".to_string(),
        input_types: vec!["optical".to_string(), "chemical".to_string()],
        operation: "photochemical_correlation".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "Photons drive chemical reactions".to_string(),
                applies: true,
            },
            Criterion {
                name: "predictive_power".to_string(),
                description: "Light dose predicts reaction yield".to_string(),
                applies: true,
            },
            Criterion {
                name: "information_gain".to_string(),
                description: "Spectral selectivity reveals reaction pathways".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "Photocatalyst efficiency testing".to_string(),
            signal_a_example: "UV-Vis spectrophotometer".to_string(),
            signal_b_example: "Gas chromatograph".to_string(),
            expected_result: "Quantum efficiency measurement".to_string(),
        }],
        citations: vec![
            "Turro et al. (2010) - Modern Molecular Photochemistry".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    // Pattern 18: Strain-Stress Material Testing
    hashes.push(add_pattern(MixingPattern {
        name: "Strain-Stress Constitutive Relation".to_string(),
        input_types: vec!["strain".to_string(), "stress".to_string()],
        operation: "constitutive_modeling".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "Stress causes strain via material elasticity".to_string(),
                applies: true,
            },
            Criterion {
                name: "temporal_stability".to_string(),
                description: "Material properties are intrinsic".to_string(),
                applies: true,
            },
            Criterion {
                name: "compressibility".to_string(),
                description: "Linear elasticity allows compact representation".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "Material characterization".to_string(),
            signal_a_example: "Strain gauge rosette".to_string(),
            signal_b_example: "Load cell".to_string(),
            expected_result: "Young's modulus and Poisson's ratio".to_string(),
        }],
        citations: vec![
            "Timoshenko & Goodier (1970) - Theory of Elasticity".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    // Pattern 19: Magnetic-Electromagnetic Hall Effect
    hashes.push(add_pattern(MixingPattern {
        name: "Magnetic-EM Hall Effect".to_string(),
        input_types: vec!["magnetic".to_string(), "electromagnetic".to_string()],
        operation: "hall_effect_correlation".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "Magnetic field deflects charge carriers in conductor".to_string(),
                applies: true,
            },
            Criterion {
                name: "predictive_power".to_string(),
                description: "B field predicts Hall voltage".to_string(),
                applies: true,
            },
            Criterion {
                name: "temporal_stability".to_string(),
                description: "Lorentz force law is universal".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "Current sensing".to_string(),
            signal_a_example: "Hall effect sensor".to_string(),
            signal_b_example: "Current probe".to_string(),
            expected_result: "Non-invasive current measurement".to_string(),
        }],
        citations: vec![
            "Hall, E.H. (1879) - On a New Action of the Magnet on Electric Currents".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    // Pattern 20: Ultrasonic-Vibration Nondestructive Testing
    hashes.push(add_pattern(MixingPattern {
        name: "Ultrasonic-Vibration NDT".to_string(),
        input_types: vec!["ultrasonic".to_string(), "vibration".to_string()],
        operation: "resonance_analysis".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "Ultrasonic waves excite structural resonances".to_string(),
                applies: true,
            },
            Criterion {
                name: "information_gain".to_string(),
                description: "High-freq ultrasound + low-freq vibration = full modal spectrum".to_string(),
                applies: true,
            },
            Criterion {
                name: "predictive_power".to_string(),
                description: "Defects shift resonant frequencies".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "Composite material inspection".to_string(),
            signal_a_example: "Ultrasonic transducer".to_string(),
            signal_b_example: "Laser vibrometer".to_string(),
            expected_result: "Detection of delamination or voids".to_string(),
        }],
        citations: vec![
            "ASTM E2001 - Resonant Ultrasound Spectroscopy".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    // Pattern 21: Infrared-Temperature Pyrometry
    hashes.push(add_pattern(MixingPattern {
        name: "Infrared-Temperature Pyrometry".to_string(),
        input_types: vec!["infrared".to_string(), "temperature".to_string()],
        operation: "stefan_boltzmann_correlation".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "Stefan-Boltzmann law: P = σT⁴".to_string(),
                applies: true,
            },
            Criterion {
                name: "temporal_stability".to_string(),
                description: "Blackbody radiation is universal".to_string(),
                applies: true,
            },
            Criterion {
                name: "predictive_power".to_string(),
                description: "Temperature predicts IR radiance".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "Industrial furnace monitoring".to_string(),
            signal_a_example: "IR pyrometer".to_string(),
            signal_b_example: "Thermocouple".to_string(),
            expected_result: "Emissivity-corrected temperature".to_string(),
        }],
        citations: vec![
            "Stefan, J. (1879) - Über die Beziehung zwischen der Wärmestrahlung".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    // Pattern 22: Seismic-Vibration Ground Motion
    hashes.push(add_pattern(MixingPattern {
        name: "Seismic-Vibration Ground Motion".to_string(),
        input_types: vec!["seismic".to_string(), "vibration".to_string()],
        operation: "ground_motion_correlation".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "Seismic waves cause ground vibration".to_string(),
                applies: true,
            },
            Criterion {
                name: "compressibility".to_string(),
                description: "Same phenomenon, different sensor types".to_string(),
                applies: true,
            },
            Criterion {
                name: "temporal_stability".to_string(),
                description: "Direct mechanical coupling".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "Earthquake site characterization".to_string(),
            signal_a_example: "Broadband seismometer".to_string(),
            signal_b_example: "Strong motion accelerometer".to_string(),
            expected_result: "Full dynamic range ground motion recording".to_string(),
        }],
        citations: vec![
            "USGS - Strong Motion Instrumentation".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    // Pattern 23: Radio-Electromagnetic Antenna Theory
    hashes.push(add_pattern(MixingPattern {
        name: "Radio-EM Antenna Radiation".to_string(),
        input_types: vec!["radio".to_string(), "electromagnetic".to_string()],
        operation: "antenna_pattern_correlation".to_string(),
        validation_criteria: vec![
            Criterion {
                name: "physical_causation".to_string(),
                description: "Radio IS electromagnetic radiation".to_string(),
                applies: true,
            },
            Criterion {
                name: "temporal_stability".to_string(),
                description: "Same physical phenomenon".to_string(),
                applies: true,
            },
            Criterion {
                name: "compressibility".to_string(),
                description: "Identical signal, different terminology".to_string(),
                applies: true,
            },
        ],
        examples: vec![Example {
            description: "Antenna far-field measurement".to_string(),
            signal_a_example: "Radio receiver".to_string(),
            signal_b_example: "E-field probe".to_string(),
            expected_result: "Antenna radiation pattern".to_string(),
        }],
        citations: vec![
            "Balanis, C.A. (2005) - Antenna Theory".to_string(),
        ],
        contributed_by: "system".to_string(),
        timestamp: sys_time()?,
    })?);

    Ok(hashes)
}
