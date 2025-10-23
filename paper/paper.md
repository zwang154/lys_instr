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

However, building such a system remains nontrivial for researchers. At the low level, specific instrument methods tightly coupled to diverse communication protocols (e.g., TCP/IP, VISA, serial, etc.) limit interchangeability and flexibility across systems. At the high level, coordinating workflows involving conditional logic, iterative processes, and advanced algorithms from different libraries can lead to redundant implementations of similar functionality across different contexts. Moreover, designing graphical user interfaces (GUIs) for these low- and high-level functionalities typically involves complex multithreading, which requires familiarity with GUI libraries such as `Qt` and the underlying operating system (OS) event-handling mechanisms. Existing frameworks such as`QCoDeS` [@QCoDeS], `PyMeasure` [@PyMeasure], `PyLabControl` [@PyLabControl], `LabVIEW` [@LabVIEW], and `MATLAB`'s Instrument Control Toolbox [@MATLAB] provide powerful ecosystems for instrument control and measurement scripting, but require users to handle low-level communications and high-level workflow logic themselves. These challenges impose substantial overhead on researchers designing custom measurement systems.

To address these issues, we introduce `lys_instr`—an object-oriented framework that abstracts common control patterns from experiment-specific implementations, reducing coding and design costs while enabling flexible and efficient automation.


# Design Philosophy

`lys_instr` adopts a three-layer architecture based on levels of abstraction, separating individual instrument control, workflow coordination, and control system assembly. Each layer applies object-oriented design patterns in GoF [@Gamma:1994], suited to its role, enhancing flexibility, modularity, and ease of use. The framework builds on the `lys` platform, leveraging its powerful multidimensional data visualization capabilities.

1. Base Layer: Individual Instrument Control

  This layer provides low-level abstractions that standardizes core instrument functionalities—primarily motors and detectors. Measurement systems typically involve two types of controllers: *motor*s, which adjust experimental parameters such as external fields, temperature, or physical positions, and *detector*s, which record experimental data, e.g., cameras, spectrometers. Concrete device implementations are separated from these interfaces, following the *Template Method* design pattern. Independent automatic threading allows each instrument to operate asynchronously, ensuring responsive operation without blocking other instruments or the GUI. Users can create standardized objects for integration into *lys_instr* with minimal device-specific coding. Additionally, every Base Layer component includes a GUI by default, removing the need for users to create one manually.

2. Intermediate Layer: Workflow Coordination

  This layer provides high-level abstractions, including the GUI, to coordinate Base Layer instruments for common experimental tasks. Many measurements share similar workflows. A representative example would be a *scan* process, recording experimental data sequentially while scanning parameters such as fields, temperature, or positions. Owing to the standardization of the instrument in the base layer, these similar workflows can be implemented with common algorithms by *Bridge* and *Composite* design patterns. *lys_instr* provides a set of such high-level functionalities commonly required across experiments. Moreover, the GUI interacts with components via signals, following the *Observer* design pattern, ensuring low coupling and high extensibility.

3. Top Layer: Control-System Assembly

  This layer enables flexible assembly of components from the Base and Intermediate Layers into a complete control system, on both the character user interface (CUI) and GUI levels. Following the *Mediator* design pattern, it manages connections among abstract devices (and, through the Base Layer, the corresponding real hardware) to enable automatic data flow, and organizes the GUI for user interaction. This grants users maximum freedom to construct tailored control systems without managing complex aspects such as inter-device communication or multi-threading. Several typical GUI templates are also provided for quick hands-on use.


# Example of Constructed GUI

With `lys_instr`, users can easily construct a GUI like the one shown in \autoref{fig:fig1}. The `lys_instr` window is embedded in the `lys` subwindow, with Sector A for storage, Sector B for detector, and the `Motor` tab in Sector C. Multi-dimensional, nested scan sequences can be defined via the visual interface in the `Scan` tab in Sector C. `lys` tools in the outer window tabs allow customization of data display, enabling advanced, on-the-fly customization of data visualization.

![Example GUI of *lys_instr*. The main window, embedded in the *lys* window, is organized into three sectors: Storage panel (A), Detector panel (B), and Motor and Scan tabs (C). The Scan tab enables dynamic configuration of mutli-dimensional, nested experimental workflows.\label{fig:fig1}](fig1.png)


# Projects using the software

`lys_instr` has been deployed in complex, real-world scientific instruments, supporting multiple peer-reviewed publications. It automates Ultrafast Transmission Electron Microscopy (UTEM) at the RIKEN Center for Emergent Matter Science, coordinating ultrafast laser excitation and pulsed electron beam detection in pump–probe experiments [@Nakamura:2020; @Nakamura:2021a; @Nakamura:2022; @Nakamura:2023a; @Shimojima:2021; @Shimojima:2023a; @Shimojima:2023b; @Koga:2024]. It enables precise control of electromagnetic lenses and electron deflectors for advanced microscopy involving electron-beam precession, a capability that would be difficult to achieve without `lys_instr` [@Shiratori:2024; @Hayashi:2025].


# Acknowledgements

We acknowledge valuable comments from Takahiro Shimojima and Kyoko Ishizaka. This work was partially supported by a Grant-in-Aid for Scientific Research (KAKENHI) (Grant No. ).
