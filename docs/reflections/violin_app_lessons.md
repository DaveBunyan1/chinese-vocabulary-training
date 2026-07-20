# Engineering Reflection: From Violin Audio Pipeline to DDD Architecture

## Background

Prior to building this Chinese Learning Platform, I developed a real-time Violin Practice App centered around live audio capture via `sounddevice`, signal processing, and pitch evaluation. While functional as a proof of concept, the project suffered from architectural friction that slowed development over time.

This document captures the key engineering lessons learned from that experience and explains how they shaped the design of this platform—and how they will guide the upcoming **v2 architecture of the Violin App**.

---

## Key Friction Points & Architectural Pivots

### 1. The "Spike First, Model Later" Trap

- **What Happened:** Because I was working with unfamiliar audio hardware APIs (`sounddevice`, NumPy processing), I built the application outwards from the hardware stream. Business logic (scoring pitches, practice state) was written directly inside audio callback buffers.
- **The Impact:** Separating the UI from the processing engine became nearly impossible. Changes to how pitches were detected broke practice tracking logic.
- **The Pivot for This Project:** I applied **Clean Architecture and DDD**. The domain model (`Sentence`, `UserVocabularyProfile`) is 100% pure Python with zero external imports. `jieba` and external LLMs are treated purely as replaceable infrastructure adapters.
- **Future Violin App v2 Plan:** Wrap the audio input pipeline in an `AudioStreamInputPort` interface. The pitch evaluation domain will operate on raw numerical arrays, completely decoupled from `sounddevice` or any physical microphone interface.

---

### 2. Retrofitted Testing vs. Test-Driven Design

- **What Happened:** Writing tests _after_ building tightly coupled audio pipelines felt like a chore. Every minor refactor broke retrofitted tests, causing test maintenance overhead to explode until testing was largely abandoned.
- **The Impact:** Velocity slowed down significantly as the codebase grew, because every change required manual testing.
- **The Pivot for This Project:** Enforced **strict TDD using In-Memory Fakes**. By relying on the Repository pattern, I can write fast unit tests for domain aggregates without spinning up databases or network calls.
- **Future Violin App v2 Plan:** Build a synthetic signal generator adapter (`MockAudioStreamAdapter`) that feeds pre-recorded pitch arrays into the domain, allowing 100% offline, deterministic TDD for violin analysis.

---

### 3. Observability as an Afterthought

- **What Happened:** Debugging pitch tracking errors or latency bottlenecks required scattering `print()` statements throughout processing loops.
- **The Impact:** Root-cause analysis was slow and inefficient.
- **The Pivot for This Project:** Integrating **OpenTelemetry and structured JSON logging (`Structlog`)** at the application boundary from the first commit.

### 4. Global Singletons, Circular Imports, and the "Developer Velocity" Tradeoff

- **What Happened:** In the initial implementation, configuration values, database/audio handles, and state stores were instantiated as global singletons inside module-level files and imported directly wherever needed.
- **The Impact:** As the application grew, these cross-dependencies collapsed into fragile circular import loops (`Module A imports Module B, which imports Module A`). Untangling these dependencies at runtime required hacky workarounds, slowing development down significantly.
- **The Pivot & Resolution:**
  1. **Runtime Dependency Graph (Dependency Injection):** Instead of module-level singletons, dependencies are instantiated at the application entry point and explicitly injected inward into services and handlers via standard Python constructors (`__init__`).
  2. **Valuing Developer Velocity over Micro-Optimizations:** In Python, passing explicit dependency instances through an inversion-of-control (IoC) graph or container introduces negligible runtime overhead (a few nanoseconds per method call). Accepting this tiny execution tradeoff delivers massive gains in developer velocity, clean modularity, and effortless unit testing.

- **Future Violin App v2 Plan:** Replace all global state imports with an explicit application startup context that builds the dependency graph on launch.

---

## Conclusion

Building the violin app was an invaluable learning experience. It highlighted the difference between _code that works_ and _architecture that scales_. This Chinese Practice Platform represents the application of those hard-learned lessons—and serves as the blueprint for rebuilding the Violin Practice App v2.
