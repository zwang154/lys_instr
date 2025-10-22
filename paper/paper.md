---
title: 'lys_instr: A Python Package for Automating Scientific Measurements'
tags:
  - Python
  - instrument control
  - scientific measurements
authors:
  - name: Ziqian Wang
    orcid: 0000-0002-0282-5941
    corresponding: true
    affiliation: 1, 2
  - name: Hidenori Tsuji
    affiliation: 2
  - name: Toshiya Shiratori
    orcid: 0009-0007-6199-1548
    affiliation: 3
  - name: Asuka Nakamura
    orcid: 0000-0002-3010-9475
    affiliation: 2, 3
affiliations:
 - name: Research Institute for Quantum and Chemical Innovation, Institutes of Innovation for Future Society, Nagoya University, Japan
   index: 1
   ror: 04chrp450
 - name: RIKEN Center for Emergent Matter Science, Japan
   index: 2
   ror: 03gv2xk61
 - name: Department of Applied Physics, The University of Tokyo, Japan
   index: 3
   ror: 057zh3y96
date: 14 October 2025
bibliography: paper.bib
---

# Summary

Modern experiments increasingly demand automation frameworks capable of coordinating diverse scientific instruments while remaining flexible and easy to customize. Existing solutions, however, often require substantial adaptation or manual handling of low-level communication and threading. We present `lys_instr`, a Python package that addresses these challenges through an object-oriented, multi-layered architecture for instrument control, workflow coordination, and GUI construction. It enables researchers to rapidly build responsive, asynchronous measurement systems with minimal coding effort. Seamlessly integrated with the `lys` platform [@Nakamura:2023], `lys_instr` unifies experiment control, data acquisition, and visualization, offering an efficient foundation for next-generation, automation-driven experimental research.


# Statement of need

Modern scientific research increasingly relies on comprehensive measurements across wide parameter spaces to fully understand physical phenomena. As experiments grow in complexity—with longer measurement times and a greater diversity of instruments—efficient automation has become essential. Measurement automation is now evolving beyond simple parameter scans toward informatics-driven, condition-based optimization, paving the way for AI-assisted experimental workflow management. This progress demands robust software infrastructure capable of high integration and flexible logic control.

However, building such a system remains nontrivial for researchers. At the low level, specific instrument methods tightly coupled to diverse communication protocols (e.g., TCP/IP, VISA, serial, etc.) limit interchangeability and flexibility across systems. At the high level, coordinating workflows involving conditional logic, iterative processes, and advanced algorithms from different libraries can lead to redundant implementations of similar functionality across different contexts. Moreover, designing GUIs for these low- and high-level functionalities typically requires complex multithreading, further increasing implementation costs. Existing frameworks such as`QCoDeS` [@QCoDeS], `PyMeasure` [@PyMeasure], `PyLabControl` [@PyLabControl], `LabVIEW` [@LabVIEW], and `MATLAB`'s Instrument Control Toolbox [@MATLAB] provide powerful ecosystems for instrument control and measurement scripting, but require users to handle low-level communications and high-level workflow logic themselves. These challenges impose substantial overhead on researchers designing custom measurement systems.

To address these issues, we introduce `lys_instr`—an object-oriented framework that abstracts common control patterns from experiment-specific implementations, reducing coding and design costs while enabling flexible and efficient automation.


# Design Philosophy

`lys_instr` adopts a three-layer architecture based on multiple object-oriented design patterns to maximize flexibility, modularity and ease of use.

1. Base Level: Instrument Abstraction

  This layer standardizes core instrument functionalities—motors, detectors, and storage—through abstract interfaces. Concrete device implementations are separated from these interfaces, following the *Template Method* design pattern. Independent automatic multi-threading management allows each instrument to operate asynchronously, ensuring responsive operation without blocking other instruments or the GUI.

2. Intermediate Level: Workflow Coordination

  This layer provides high-level abstractions, including the GUI, to coordinate base instruments for general experimental tasks. It standardizes common operations such as *move-and-detect*, scans, and nested scan sequences without requiring knowledge of concrete instrument implementations, following the *Bridge* design pattern. The GUI interacts with components via signals, adhering to the *Observer* design pattern, ensuring low coupling and high extensibility. Concepts from the *Composite* design pattern are also employed to efficiently manage nested scan configurations.

3. Top Level: Control Panel Construction

  The highest layer supports flexible assembly of the measurement GUI. Following the *Mediator* design pattern, it manages connections among abstract devices (and, through the base level, the corresponding real hardware) and organizes the GUI for user control. This grants users maximum freedom to construct tailored control systems without managing complex aspects such as inter-device communication or multi-threading.


# Key Functionalities

`lys_instr` provides a straightforward user interface—illustrated in the preliminary example in Figure 1—for integrated instrument/data management and declarative workflow control.  

**Integrated Instrument/Data Management:** The *Base Layer* ensures asynchronous operation across all instruments (Sector A for storage, Sector B for detector, and the *Motor* tab in C), keeping each GUI component responsive during cooperative measurements.  

**Declarative Workflow Management:** Users can define multi-dimensional, nested scan sequences (*MultiScan*) via a visual interface (the *Scan* tab in Sector C). Built on the *Intermediate Layer* abstraction, these workflows hierarchically coordinate motors and detectors, enabling sophisticated experiments without any low-level coding.  

In addition, `lys_instr` supports user-defined GUI layouts through the Top Layer. It further enhances extensibility through seamless integration with the `lys` platform (the outer window with tabs), enabling advanced on-the-fly customization of data visualization.


# Projects using the software

`lys_instr` has been deployed in complex, real-world scientific instruments, supporting multiple peer-reviewed publications. It automates Ultrafast Transmission Electron Microscopy (UTEM) at RIKEN Center for Emergent Matter Science, coordinating ultrafast laser excitation and pulsed electron beam detection in pump–probe experiments [@Nakamura:2020; @Nakamura:2021a; @Nakamura:2022; @Nakamura:2023a; @Shimojima:2021; @Shimojima:2023a; @Shimojima:2023b], and it controls electromagnetic lenses and electron deflectors for advanced microscopy with electron-beam precession [@Shiratori:2024; @Hayashi:2025].


# Acknowledgements

We acknowledge valuable comments from Takahiro Shimojima and Kyoko Ishizaka. This work was partially supported by a Grant-in-Aid for Scientific Research (KAKENHI) (Grant No. ).
