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

However, building such a system remains nontrivial for researchers. At the low level, specific instrument methods tightly coupled to diverse communication protocols (e.g., TCP/IP, VISA, serial, etc.) limit interchangeability and flexibility across systems. At the high level, coordinating workflows involving conditional logic, iterative processes, and advanced algorithms from different libraries can lead to redundant implementations of similar functionality across different contexts. Moreover, designing graphical user interfaces (GUIs) for these low- and high-level functionalities typically involves complex multithreading, which requires familiarity with GUI libraries such as `Qt` and the underlying operating system (OS) event-handling mechanisms. Existing frameworks such as `QCoDeS` [@QCoDeS], `PyMeasure` [@PyMeasure], `PyLabControl` [@PyLabControl], `LabVIEW` [@LabVIEW], and `MATLAB`'s Instrument Control Toolbox [@MATLAB] provide powerful ecosystems for instrument control and measurement scripting, but require users to handle low-level communications and high-level workflow logic themselves. These challenges impose substantial overhead on researchers designing custom measurement systems.

To address these issues, we introduce `lys_instr`—an object-oriented framework that abstracts common control patterns from experiment-specific implementations, reducing coding and design costs while enabling flexible and efficient automation.


# Design philosophy

`lys_instr` adopts a three-layer architecture organized by functional separation: Base Layer for device controller abstraction, Top Layer for workflow coordination, and Connection Layer in between for complete control-system assembly (\autoref{fig:fig1}). Each layer applies object-oriented design patterns from GoF [@Gamma:1994], according to its responsibilities, enhancing flexibility, modularity, and usability. The framework builds on the `lys` platform, leveraging its powerful multidimensional data visualization capabilities.

![Schematic of the code architecture of `lys_instr`.\label{fig:fig1}](fig1.png)

1. Base Layer: Device Controller Abstraction

  This layer defines abstract interfaces that standardize core instrument controllers. The interfaces expose hooks for concrete implementations to override, following the *Template Method* design pattern. Typically, most measurement systems include two types of controllers: *motor*s, which adjust experimental parameters such as external fields, temperature, or physical positions, and *detector*s, which record experimental data, e.g., cameras, spectrometers. Accordingly, `lys_instr` provides standardized *motor* and *detector* interfaces that unify controller behavior, allowing higher layers to operate on different devices uniformly through common interface methods. Users only need to provide device-specific subclasses that inherit from these interfaces to handle communication with their respective hardware devices. Moreover, each controller manages its own thread(s), ensuring responsiveness and asynchronous operation without blocking other controllers or the GUIs in higher layers. This structure enables users to create controller objects hat can be readily integrated into higher-level workflows with minimal device-specific coding.


2. Top Layer: Workflow Coordination

  This layer coordinates Base Layer controllers to construct experimental workflows common across many setups. Most measurements share similar procedural structures, such as a *scan* process in which data are sequentially recorded while parameters like fields, temperature, or positions are varied. These workflows are standardized using the abstract interfaces defined in the Base Layer, independent of any specific hardware devices, following the *Bridge* and *Composite* design patterns. For example, `lys_instr` provides a standardized *scan* routine that calls *motor* and *detector* interface methods without requiring knowledge of the underlying concrete implementations. This abstraction allows such workflows to be reused across different hardware configurations, greatly improving coding efficiency. In addition, this layer includes prebuilt GUI components corresponding to each Base Layer interface, enabling direct GUI-based control of controllers through the same abstract methods. This design cleanly separates workflow logic from device-specific details, simplifying extension to complex measurement systems. Moreover, the GUI communicates with Base Layer interfaces via signal-slot connections, following the *Observer* design pattern to ensure low coupling and high extensibility. With this layer, users can design measurement workflows from scratch without manually creating GUI components.

3. Connection Layer: Control-System Assembly

  This layer enables flexible assembly of components from the Base and Top Layers into a complete control system by managing connections within and across layers. Following the *Mediator* design pattern, it connects abstract Base Layer interfaces (and, through them, the corresponding hardware devices) to enable automatic data flow, and links GUI components to their respective interfaces, fully hiding device-specific implementations from this layer and above. It also organizes the GUI components into a cohesive application for user interaction. This design grants users maximum freedom to construct tailored control systems without handling low-level tasks such as inter-device communication or multi-threading. Several prebuilt GUI templates for common scenarios are provided for quick hands-on use.

Overall, `lys_instr` provides prebuilt support for standard device controllers, common experimental workflows, and GUI components and assemblies, so users generally need to implement only device-specific subclasses to handle communication with their hardware. This enables rapid integration of new instruments into automated measurement workflows with minimal coding and design effort.


# Example of Constructed GUI

With `lys_instr`, users can easily construct a GUI like the one shown in \autoref{fig:fig2}. The `lys_instr` window is embedded in the `lys` subwindow, with Sector A for storage, Sector B for detector, and the `Motor` tab in Sector C. Multi-dimensional, nested scan sequences can be defined via the visual interface in the `Scan` tab in Sector C. `lys` tools in the outer window tabs allow customization of data display, enabling advanced, on-the-fly customization of data visualization.

![Example GUI of `lys_instr`. The main window, embedded in the `lys` window, contains three sectors: Storage panel (A), Detector panel (B), and Motor and Scan tabs (C). The Scan tab enables dynamic configuration of multi-dimensional, nested experimental workflows.\label{fig:fig2}](fig2.png)


# Projects using the software

`lys_instr` has been deployed in complex, real-world scientific instruments, supporting multiple peer-reviewed publications. It automates Ultrafast Transmission Electron Microscopy (UTEM) at the RIKEN Center for Emergent Matter Science, coordinating ultrafast laser excitation and pulsed electron beam detection in pump–probe experiments [@Nakamura:2020; @Nakamura:2021a; @Nakamura:2022; @Nakamura:2023a; @Shimojima:2021; @Shimojima:2023a; @Shimojima:2023b; @Koga:2024]. It enables precise control of electromagnetic lenses and electron deflectors for advanced microscopy involving electron-beam precession, a capability that would be difficult to achieve without `lys_instr` [@Shiratori:2024; @Hayashi:2025].


# Acknowledgements

We acknowledge valuable comments from Takahiro Shimojima and Kyoko Ishizaka. This work was partially supported by a Grant-in-Aid for Scientific Research (KAKENHI) (Grant No. ).


# References
