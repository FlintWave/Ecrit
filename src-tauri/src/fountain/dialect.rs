use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Dialect {
    pub id: String,
    pub name: String,
    pub description: String,
    pub paper: PaperSize,
    pub extra_elements: Vec<ExtraElement>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub enum PaperSize {
    USLetter,
    A4,
}

impl PaperSize {
    pub fn width_inches(&self) -> f64 {
        match self {
            PaperSize::USLetter => 8.5,
            PaperSize::A4 => 8.27,
        }
    }

    pub fn height_inches(&self) -> f64 {
        match self {
            PaperSize::USLetter => 11.0,
            PaperSize::A4 => 11.69,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExtraElement {
    pub name: String,
    pub tag: String,
}

pub fn builtin_dialects() -> Vec<Dialect> {
    vec![
        Dialect {
            id: "fountain/core".into(),
            name: "Standard Screenplay".into(),
            description: "The modern spec standard — master scenes, Courier Prime 12pt, US Letter.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![],
        },
        Dialect {
            id: "fountain+shooting".into(),
            name: "Shooting Script".into(),
            description: "Numbered scenes, locked pages, revision colors for production.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![],
        },
        Dialect {
            id: "fountain+studio47".into(),
            name: "Classic Studio 1930s–50s".into(),
            description: "Vintage studio format with period conventions.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![],
        },
        Dialect {
            id: "fountain+a4".into(),
            name: "European A4".into(),
            description: "Metric standard — A4 paper with adjusted margins.".into(),
            paper: PaperSize::A4,
            extra_elements: vec![],
        },
        Dialect {
            id: "fountain+multicam".into(),
            name: "US Multi-Camera Sitcom".into(),
            description: "Multi-camera format with underlined slug lines and double-spaced dialogue.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![],
        },
        Dialect {
            id: "fountain+bbc-screen".into(),
            name: "BBC Screenplay".into(),
            description: "BBC television screenplay format on A4.".into(),
            paper: PaperSize::A4,
            extra_elements: vec![],
        },
        Dialect {
            id: "fountain+bbc-scene".into(),
            name: "BBC Scene Style".into(),
            description: "BBC scene-style television format on A4.".into(),
            paper: PaperSize::A4,
            extra_elements: vec![],
        },
        Dialect {
            id: "fountain+radio-scene".into(),
            name: "BBC Radio Scene Style".into(),
            description: "BBC radio drama in scene style on A4.".into(),
            paper: PaperSize::A4,
            extra_elements: vec![],
        },
        Dialect {
            id: "fountain+radio-cue".into(),
            name: "BBC Radio Cue Style".into(),
            description: "BBC radio drama with numbered cues on A4.".into(),
            paper: PaperSize::A4,
            extra_elements: vec![],
        },
        Dialect {
            id: "fountain+audio-us".into(),
            name: "US Audio Drama".into(),
            description: "American audio drama format on US Letter.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![],
        },
        Dialect {
            id: "fountain+comic-full".into(),
            name: "Full Script — DC House".into(),
            description: "Full script comic format with page/panel descriptions.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![
                ExtraElement { name: "Panel".into(), tag: "panel".into() },
                ExtraElement { name: "Caption".into(), tag: "caption".into() },
                ExtraElement { name: "SFX".into(), tag: "sfx".into() },
            ],
        },
        Dialect {
            id: "fountain+comic-plot".into(),
            name: "Marvel Method".into(),
            description: "Plot-first comic format for artist collaboration.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![
                ExtraElement { name: "Panel".into(), tag: "panel".into() },
            ],
        },
        Dialect {
            id: "fountain+comic-lean".into(),
            name: "Panel-per-line".into(),
            description: "Minimal comic format, one panel per line.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![],
        },
        Dialect {
            id: "fountain+comic-gn".into(),
            name: "Graphic Novel".into(),
            description: "Long-form graphic novel script format.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![
                ExtraElement { name: "Panel".into(), tag: "panel".into() },
                ExtraElement { name: "Caption".into(), tag: "caption".into() },
            ],
        },
        Dialect {
            id: "fountain+stage-us".into(),
            name: "US Stage Play".into(),
            description: "American stage play format on US Letter.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![
                ExtraElement { name: "Stage Direction".into(), tag: "stage_dir".into() },
            ],
        },
        Dialect {
            id: "fountain+stage-uk".into(),
            name: "UK Stage Play".into(),
            description: "British stage play format on A4.".into(),
            paper: PaperSize::A4,
            extra_elements: vec![
                ExtraElement { name: "Stage Direction".into(), tag: "stage_dir".into() },
            ],
        },
        Dialect {
            id: "fountain+branch".into(),
            name: "Branching Dialogue".into(),
            description: "Interactive branching dialogue for games.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![
                ExtraElement { name: "Choice".into(), tag: "choice".into() },
                ExtraElement { name: "Branch".into(), tag: "branch".into() },
            ],
        },
        Dialect {
            id: "fountain+barks".into(),
            name: "Barks & Systemic VO".into(),
            description: "Short voice lines and systemic dialogue for games.".into(),
            paper: PaperSize::USLetter,
            extra_elements: vec![
                ExtraElement { name: "Bark".into(), tag: "bark".into() },
                ExtraElement { name: "Context".into(), tag: "context".into() },
            ],
        },
    ]
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FormatCategory {
    pub name: String,
    pub description: String,
    pub formats: Vec<String>,
}

pub fn format_categories() -> Vec<FormatCategory> {
    vec![
        FormatCategory {
            name: "Feature Film".into(),
            description: "Master-scene screenplays, from the modern spec standard back to the studio-era house styles.".into(),
            formats: vec![
                "fountain/core".into(),
                "fountain+shooting".into(),
                "fountain+studio47".into(),
                "fountain+a4".into(),
            ],
        },
        FormatCategory {
            name: "Television".into(),
            description: "Single-camera drama, multi-camera sitcom, and BBC formats.".into(),
            formats: vec![
                "fountain/core".into(),
                "fountain+multicam".into(),
                "fountain+bbc-screen".into(),
                "fountain+bbc-scene".into(),
            ],
        },
        FormatCategory {
            name: "Audio & Radio".into(),
            description: "BBC radio drama and US audio drama formats.".into(),
            formats: vec![
                "fountain+radio-scene".into(),
                "fountain+radio-cue".into(),
                "fountain+audio-us".into(),
            ],
        },
        FormatCategory {
            name: "Comics & Graphic Novels".into(),
            description: "Full script, Marvel method, panel-per-line, and graphic novel formats.".into(),
            formats: vec![
                "fountain+comic-full".into(),
                "fountain+comic-plot".into(),
                "fountain+comic-lean".into(),
                "fountain+comic-gn".into(),
            ],
        },
        FormatCategory {
            name: "Stage".into(),
            description: "US and UK stage play formats.".into(),
            formats: vec![
                "fountain+stage-us".into(),
                "fountain+stage-uk".into(),
            ],
        },
        FormatCategory {
            name: "Interactive".into(),
            description: "Branching dialogue and systemic voice-over for games.".into(),
            formats: vec![
                "fountain+branch".into(),
                "fountain+barks".into(),
            ],
        },
    ]
}
