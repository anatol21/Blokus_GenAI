classDiagram
    %% Core System APIs (Functional interfaces provided by engine.py)
    class Engine_API {
        <<interface>>
        new_game()
        validate_move()
        apply_move()
        list_legal_moves()
    }

    %% High-Level Components
    class Models_and_Config {
        <<component>>
        GameState, Move
        Game Configurations
    }

    class Core_Engine {
        <<component>>
        Rules Enforcement
        State & Turn Management
    }

    class Presentation_GUI {
        <<component>>
        Visual Rendering
        Input Event Capture
    }

    class Orchestration_CLI {
        <<component>>
        Textual Interaction
        Command Parsing
    }

    %% Interface Provision (Exposed functions)
    Engine_API <|.. Core_Engine : provides

    %% Component Dependencies
    Core_Engine ..> Models_and_Config : depends on
    
    Presentation_GUI ..> Engine_API : calls functions
    Presentation_GUI ..> Models_and_Config : uses data structures
    
    Orchestration_CLI ..> Engine_API : calls functions
    Orchestration_CLI ..> Models_and_Config : uses data structures
