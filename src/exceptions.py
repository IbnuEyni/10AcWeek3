"""Custom exceptions for Document Intelligence Refinery"""


class DocumentRefineryError(Exception):
    """Base exception for all refinery errors"""
    pass


class DocumentValidationError(DocumentRefineryError):
    """Raised when document validation fails"""
    pass


class TriageError(DocumentRefineryError):
    """Raised when document triage fails"""
    pass


class ExtractionError(DocumentRefineryError):
    """Raised when extraction fails"""
    pass


class StrategyError(ExtractionError):
    """Raised when extraction strategy fails"""
    pass


class ConfidenceThresholdError(ExtractionError):
    """Raised when confidence is below acceptable threshold"""
    pass


class BudgetExceededError(ExtractionError):
    """Raised when extraction cost exceeds budget"""
    
    def __init__(self, estimated_cost: float, budget: float):
        self.estimated_cost = estimated_cost
        self.budget = budget
        super().__init__(f"Cost ${estimated_cost:.2f} exceeds budget ${budget:.2f}")


class APIError(DocumentRefineryError):
    """Raised when external API call fails"""
    pass


class ConfigurationError(DocumentRefineryError):
    """Raised when configuration is invalid"""
    pass
