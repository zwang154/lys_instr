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
 - name: Institutes of Innovation for Future Society, Nagoya University, Japan
   index: 1
   ror: 04chrp450
 - name: RIKEN Center for Emergent Matter Science, Japan
   index: 2
   ror: 03gv2xk61
 - name: Department of Applied Physics, The University of Tokyo, Japan
   index: 3
   ror: 057zh3y96
date: 14 November 2025
bibliography: paper.bib
---

# Summary

Modern experiments increasingly demand automation frameworks that coordinate diverse scientific instruments while remaining flexible and customizable. Developing custom measurement systems, however, often requires explicit management of low-level device communication and concurrency, resulting in substantial development overhead. We present `lys_instr`, a Python package that addresses these challenges through an object-oriented, three-layer architecture for instrument control, workflow coordination, and GUI construction. It enables researchers to construct responsive, asynchronous measurement systems by reusing instrument abstractions, workflow logic, and GUI components across hardware configurations. Integrated with the `lys` platform [@Nakamura:2023], `lys_instr` provides a common environment for experiment control, data acquisition, and multidimensional visualization.

# Statement of need

Modern scientific research increasingly requires measurements across wide parameter spaces to elucidate physical phenomena. As experiments involve longer acquisition times and more diverse instruments, efficient automation becomes increasingly valuable. Measurement workflows may also incorporate informatics-driven, condition-based optimization through external Python libraries, motivating reusable programmatic interfaces.

However, building such a measurement system remains time-consuming for researchers. At the low level, instrument-control implementations must accommodate diverse communication protocols (e.g., TCP/IP, VISA, and serial), which can limit device interchangeability and reuse across systems. At the high level, coordinating workflows that combine conditional logic, iterative processes, and advanced algorithms across multiple libraries frequently leads to redundant implementations, reducing development efficiency. For example, capturing temperature-dependent images with a camera and acquiring temperature-dependent spectra share the same general workflow: iterative temperature adjustment followed by data acquisition. Nevertheless, this logic is often implemented separately for different experiments.
Moreover, for long or complex measurements, graphical user interfaces (GUIs) provide real-time visualization, device-state monitoring, and support for manual intervention. Implementing responsive GUIs for these low- and high-level functions, however, requires familiarity with GUI frameworks and event-handling mechanisms. These impose substantial development overhead and highlight the need for a control framework that balances architectural flexibility with reduced implementation complexity.


# State of the field

Scientific instrument-control software spans environments with different priorities. LabVIEW [@LabVIEW] and MATLAB’s Instrument Control Toolbox [@MATLAB] integrate instrument communication, workflows, and GUI development. QCoDeS [@QCoDeS] and PyMeasure [@PyMeasure] provide instrument abstractions and experimental procedures. PyMoDAQ [@PyMoDAQ] combines actuator and detector plugins with dashboards and scan extensions, while Bluesky [@Bluesky] separates hardware abstraction from reusable orchestration plans and optional GUI clients. Qudi [@Qudi] explicitly separates hardware, experiment logic, and GUI layers. Atomize [@Atomize] and fsc2 [@fsc2] support script-based experiments through reusable device operations. Together, these systems establish hardware, workflow, and GUI abstractions but differ in how they integrate them and which workflows they target.

Within this landscape, the primary use case of `lys_instr` is laboratory automation in which hardware-specific instrument control is abstracted to enable reusable, hardware-independent measurement workflows. When users' instruments conform to the existing `lys_instr` interfaces, rich measurement environments integrating instrument control, workflow execution, and graphical interaction can be constructed with only a small amount of additional code. Users can therefore focus their coding efforts on the aspects that are specific to their measurements, including the implementation of new measurement strategies and algorithms, rather than repeatedly developing the underlying control infrastructure. To support this use case, `lys_instr` was developed as a distinct package with a consistent API across the three layers described below. Integration with `lys` adds multidimensional visualization and analysis to these capabilities.


# Software design

The three layers and their relationships are summarized in \autoref{fig:fig1}. Each layer applies established object-oriented design patterns [@Gamma:1994] to define how components are extended, composed, and connected.

![Schematic of the code architecture of `lys_instr`.\label{fig:fig1}](fig1.png)

1. Base Layer: Instrument Abstraction

  This layer defines standardized abstract interfaces for two principal roles in a control-and-detect workflow: *controllers*, which adjust experimental parameters such as external fields, temperature, or physical position, and *detectors*, which acquire data such as images or spectra. Following the *Template Method* pattern, the base interfaces define the device lifecycle, state monitoring, synchronization, and asynchronous execution, while subclasses implement the primitive operations required for device-specific communication. Higher layers interact with different instruments through the same methods, independently of their concrete implementations. Because background monitoring and acquisition are managed by the interfaces, other devices and GUIs can remain responsive, and device-specific subclasses can be integrated directly into higher-level workflows without reimplementing concurrency logic.

2. Top Layer: Workflow Coordination

  This layer constructs hardware-independent workflows from the Base Layer interfaces. In a *scan*, controllers vary experimental parameters while detectors acquire data at each step. Following the *Bridge* pattern, scan execution depends on controller and detector abstractions rather than concrete hardware implementations. The *Composite* pattern allows individual scan processes to be nested into multi-parameter workflows while retaining a common execution model. Prebuilt GUI components invoke the same abstract methods for direct device control and receive state and data updates through event-driven signals, following the *Observer* pattern and avoiding direct dependencies on concrete devices. Consequently, workflow and GUI logic can be reused across different hardware configurations without rebuilding standard control and coordination components.

3. Connection Layer: Control-System Assembly

  This layer assembles components from the Base and Top Layers into an interactive control system, including device interfaces, workflows, data storage, visualization, and GUI components. Following the *Mediator* pattern, it centrally manages connections within and across layers, linking GUI components to their corresponding interfaces and coordinating data flow without direct dependencies among individual components. Concrete hardware details therefore remain confined to the Base Layer, allowing system configurations and GUI layouts to be adapted without application-level implementation of inter-device communication or thread coordination. Prebuilt templates provide starting configurations that can be adapted to individual experimental setups.

Together, these layers allow new instruments to be integrated through device-specific subclasses while reusing asynchronous execution, workflow coordination, and GUI behavior. Workflows with different coordination models can be supported through additional components or customized interfaces.


# Example GUI configuration

`lys_instr` allows users to assemble GUIs suited to individual experimental setups; \autoref{fig:fig2} shows one possible configuration. Here, the `lys_instr` window is embedded in the `lys` platform, with Sector A for data storage, Sector B for detector control, and Sector C for controller operation and scan configuration. Multidimensional, nested scan sequences can be defined through the `Scan` tab, while `lys` tools in the outer window tabs allow on-the-fly customization of acquired-data visualization.

![Example GUI configuration in `lys_instr`. The main window, embedded in the `lys` window, contains three sectors: storage (A), detector control (B), and controller operation and scan configuration (C). The `Scan` tab in (C) enables configuration of multidimensional, nested experimental workflows.\label{fig:fig2}](fig2.png)


# Research impact statement

`lys_instr` has been used in experiments reported in several peer-reviewed publications. It has been used to automate ultrafast electron diffraction (UED) and ultrafast transmission electron microscopy (UTEM) systems by coordinating experimental parameters and data acquisition in pump–probe experiments using ultrafast laser excitation and pulsed electron beams [@Nakamura:2020; @Nakamura:2021a; @Nakamura:2022; @Nakamura:2023a; @Shimojima:2021; @Shimojima:2023a; @Shimojima:2023b; @Koga:2024]. It has also been used to control electromagnetic lenses and electron deflectors as part of complex microscopy workflows involving electron-beam precession [@Shiratori:2024; @Hayashi:2025].

The same interface-based workflows have been used to control transmission electron microscopes from multiple manufacturers at RIKEN Center for Emergent Matter Science and Nagoya University, demonstrating portability across hardware configurations. Integration with sister packages in the `lys` family, including `lys_em` [@lys_em] and `lys_fem` [@lys_fem], allows `lys_instr` components to participate in multi-instrument workflows while preserving modularity and extensibility.


# AI usage disclosure

Generative AI tools provided debugging suggestions during the final stages of software development. The authors implemented and reviewed all changes. Core non-GUI behavior was tested with unit tests, while GUI and hardware workflows were validated with real instruments.


# Acknowledgements

We acknowledge valuable comments from Takahiro Shimojima and Kyoko Ishizaka. This work was partially supported by Grant-in-Aid for Scientific Research (KAKENHI) Grants No. 21K13889, No. 26K17092, and No. 25K00057, and JST PRESTO Grant No. JPMJPR24JA.


# References
