using System.ComponentModel;
using System.Text.Json;
using Azure.Identity;
using CommandLine;
using CsvHelper;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using System.Globalization;

namespace HomeLoanAgent;

/// <summary>
/// Command line options for the Home Loan Agent application
/// </summary>
public class Options
{
    [Option('q', "question", Required = false, Default = "What documents do I need for a Contoso Bank loan?",
        HelpText = "The question to ask the agent")]
    public string Question { get; set; } = string.Empty;

    [Option('i', "interactive", Required = false, Default = false,
        HelpText = "Run in interactive mode to ask multiple questions")]
    public bool Interactive { get; set; }
}

/// <summary>
/// Home Loan Agent application using Semantic Kernel
/// </summary>
public class Program
{
    private static ILogger<Program>? _logger;
    private static IConfiguration? _configuration;

    public static async Task Main(string[] args)
    {
        // Parse command line arguments
        var parseResult = Parser.Default.ParseArguments<Options>(args);
        
        await parseResult.WithParsedAsync(async options =>
        {
            // Setup configuration and logging
            var host = CreateHostBuilder(args).Build();
            _logger = host.Services.GetRequiredService<ILogger<Program>>();
            _configuration = host.Services.GetRequiredService<IConfiguration>();

            try
            {
                _logger.LogInformation("Starting Home Loan Agent...");

                if (options.Interactive)
                {
                    await RunInteractiveMode();
                }
                else
                {
                    await ProcessSingleQuestion(options.Question);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "An error occurred while running the application");
                Environment.Exit(1);
            }
        });

        parseResult.WithNotParsed(errors =>
        {
            Console.WriteLine("Error parsing command line arguments:");
            foreach (var error in errors)
            {
                Console.WriteLine($"  {error}");
            }
            Environment.Exit(1);
        });
    }

    /// <summary>
    /// Creates the host builder for dependency injection and configuration
    /// </summary>
    private static IHostBuilder CreateHostBuilder(string[] args) =>
        Host.CreateDefaultBuilder(args)
            .ConfigureAppConfiguration((context, config) =>
            {
                config.AddJsonFile("appsettings.json", optional: false, reloadOnChange: true);
                config.AddEnvironmentVariables();
                config.AddUserSecrets<Program>();
            })
            .ConfigureLogging((context, logging) =>
            {
                logging.ClearProviders();
                logging.AddConsole();
            });

    /// <summary>
    /// Creates and configures the Semantic Kernel with Azure OpenAI
    /// </summary>
    private static Kernel CreateKernel()
    {
        var kernelBuilder = Kernel.CreateBuilder();

        // Get configuration values
        var endpoint = _configuration?["AzureOpenAI:Endpoint"] ?? Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT");
        var apiKey = _configuration?["AzureOpenAI:ApiKey"] ?? Environment.GetEnvironmentVariable("AZURE_OPENAI_API_KEY");
        var deploymentName = _configuration?["AzureOpenAI:DeploymentName"] ?? Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT_NAME") ?? "gpt-4o-mini";

        if (string.IsNullOrEmpty(endpoint))
        {
            throw new InvalidOperationException("Azure OpenAI endpoint is not configured. Please set AZURE_OPENAI_ENDPOINT environment variable or configure it in appsettings.json");
        }

        // Configure Azure OpenAI
        if (!string.IsNullOrEmpty(apiKey))
        {
            kernelBuilder.AddAzureOpenAIChatCompletion(deploymentName, endpoint, apiKey);
            _logger?.LogInformation("Configured Azure OpenAI with API key authentication");
        }
        else
        {
            kernelBuilder.AddAzureOpenAIChatCompletion(deploymentName, endpoint, new DefaultAzureCredential());
            _logger?.LogInformation("Configured Azure OpenAI with DefaultAzureCredential authentication");
        }

        // Add plugins
        kernelBuilder.Plugins.AddFromType<MortgageCalculatorPlugin>();

        return kernelBuilder.Build();
    }

    /// <summary>
    /// Creates a ChatCompletionAgent with the configured instructions and capabilities
    /// </summary>
    private static ChatCompletionAgent CreateHomeLoanAgent(Kernel kernel)
    {
        const string instructions = """
            Home Loan Guide is your expert assistant with over 10 years of experience in mortgage lending and loan processing. I am here to simplify the mortgage application process and support borrowers in making informed decisions about their home financing.

            My primary responsibilities include:
            1. Guiding users through the mortgage application process step-by-step.
            2. Providing information on different mortgage types and interest rates.
            3. Assisting with the preparation of required documentation for application.
            4. Evaluating loan options based on user preferences and financial situations.
            5. Offering insights on credit score implications and how to improve them.
            6. Answering questions regarding loan approvals and denials.
            7. Explaining mortgage terms and payment structures in simple language.
            8. Assisting clients in understanding the closing process and associated fees.

            I combine financial logic and document awareness to provide smart, supportive advice through every phase of the mortgage journey.

            # Form Details
            To effectively assist you, please provide answers to the following:
            - What type of mortgage are you interested in? (e.g., conventional, FHA, VA)
            - What is the purchase price of the property you are considering?
            - What is your estimated down payment amount?
            - Do you have a pre-approval letter or any existing mortgage offers?
            - What is your current credit score range, if known?
            - Are there specific concerns or questions you have about the mortgage process or options?

            # Manager Feedback
            To enhance my capabilities as a Mortgage Loan Assistant, I follow these feedback insights:
            - Provide real-time updates on application statuses to keep users informed.
            - Use clear, jargon-free language to simplify complex mortgage concepts.
            - Be proactive in offering mortgage rate comparisons and product suggestions.
            - Maintain a supportive and patient demeanor throughout the application process.
            - Follow up after application submissions to assist with documentation or next steps.

            Use the available tools to help with calculations and provide accurate information based on the loan documentation and eligibility data.
            """;

        return new ChatCompletionAgent()
        {
            Name = "HomeLoanGuide",
            Instructions = instructions,
            Kernel = kernel,
            Arguments = new KernelArguments(new AzureOpenAIPromptExecutionSettings()
            {
                FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
            })
        };
    }    /// <summary>
    /// Processes a single question with the agent
    /// </summary>
    private static async Task ProcessSingleQuestion(string question)
    {
        _logger?.LogInformation("Processing single question: {Question}", question);

        var kernel = CreateKernel();
        var agent = CreateHomeLoanAgent(kernel);

        // Add system context about available documents
        var contextMessage = await GetDocumentContext();

        Console.WriteLine($"\n=== Home Loan Agent ===");
        Console.WriteLine($"Question: {question}\n");

        // Create a list of messages with system context and user question
        var messages = new List<ChatMessageContent>
        {
            new(AuthorRole.System, contextMessage),
            new(AuthorRole.User, question)
        };        // Get agent response
        Console.Write("Agent: ");
        await foreach (var responseItem in agent.InvokeAsync(messages))
        {
            Console.WriteLine(responseItem.Message.Content);
        }

        Console.WriteLine("\n=== End of Response ===");
    }    /// <summary>
    /// Runs the agent in interactive mode
    /// </summary>
    private static async Task RunInteractiveMode()
    {
        _logger?.LogInformation("Starting interactive mode");

        Console.WriteLine("\n=== Home Loan Agent - Interactive Mode ===");
        Console.WriteLine("Ask questions about home loans and mortgage documentation.");
        Console.WriteLine("Type 'quit', 'exit', or 'q' to stop.\n");

        var kernel = CreateKernel();
        var agent = CreateHomeLoanAgent(kernel);

        // Add system context about available documents
        var contextMessage = await GetDocumentContext();
        var messages = new List<ChatMessageContent>
        {
            new(AuthorRole.System, contextMessage)
        };

        while (true)
        {
            try
            {
                Console.Write("You: ");
                var input = Console.ReadLine();

                if (string.IsNullOrWhiteSpace(input))
                    continue;

                if (input.Equals("quit", StringComparison.OrdinalIgnoreCase) ||
                    input.Equals("exit", StringComparison.OrdinalIgnoreCase) ||
                    input.Equals("q", StringComparison.OrdinalIgnoreCase))
                {
                    Console.WriteLine("Goodbye!");
                    break;
                }

                // Add user message to history
                messages.Add(new ChatMessageContent(AuthorRole.User, input));

                Console.Write("Agent: ");                // Get agent response and collect the full response
                var fullResponse = string.Empty;
                await foreach (var responseItem in agent.InvokeStreamingAsync(messages))
                {
                    if (responseItem.Message?.Content != null)
                    {
                        Console.Write(responseItem.Message.Content);
                        fullResponse += responseItem.Message.Content;
                    }
                }

                Console.WriteLine("\n");

                // Add agent response to history
                if (!string.IsNullOrEmpty(fullResponse))
                {
                    messages.Add(new ChatMessageContent(AuthorRole.Assistant, fullResponse));
                }
            }
            catch (Exception ex)
            {
                _logger?.LogError(ex, "Error processing user input");
                Console.WriteLine($"Error: {ex.Message}");
            }
        }
    }

    /// <summary>
    /// Gets document context from the available files
    /// </summary>
    private static async Task<string> GetDocumentContext()
    {
        var context = "Available documents and data:\n\n";

        try
        {
            // Read the documentation checklist
            var checklistPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Contoso_Loan_Documentation_Checklist.md");
            if (File.Exists(checklistPath))
            {
                var checklist = await File.ReadAllTextAsync(checklistPath);
                context += "LOAN DOCUMENTATION CHECKLIST:\n" + checklist + "\n\n";
            }

            // Read the loan product eligibility data
            var csvPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "loan_product_eligibility_dataset.csv");
            if (File.Exists(csvPath))
            {
                var csvContent = await File.ReadAllTextAsync(csvPath);
                context += "LOAN PRODUCT ELIGIBILITY DATA:\n" + csvContent + "\n\n";
            }
        }
        catch (Exception ex)
        {
            _logger?.LogWarning(ex, "Error reading document context files");
        }

        return context;
    }
}

/// <summary>
/// Plugin for mortgage calculations and loan-related functions
/// </summary>
public class MortgageCalculatorPlugin
{
    /// <summary>
    /// Calculates monthly mortgage payment
    /// </summary>
    [KernelFunction]
    [Description("Calculates the monthly mortgage payment based on loan amount, interest rate, and loan term")]
    public string CalculateMonthlyPayment(
        [Description("The loan amount in dollars")] double loanAmount,
        [Description("The annual interest rate as a percentage (e.g., 6.5 for 6.5%)")] double annualInterestRate,
        [Description("The loan term in years")] int loanTermYears)
    {
        try
        {
            if (loanAmount <= 0 || annualInterestRate < 0 || loanTermYears <= 0)
            {
                return "Error: Invalid input parameters. Loan amount must be positive, interest rate must be non-negative, and loan term must be positive.";
            }

            // Convert annual rate to monthly rate
            double monthlyRate = (annualInterestRate / 100) / 12;
            int numberOfPayments = loanTermYears * 12;

            // Calculate monthly payment using the formula: M = P * [r(1+r)^n] / [(1+r)^n - 1]
            double monthlyPayment;
            if (monthlyRate == 0)
            {
                // If interest rate is 0, payment is simply loan amount divided by number of payments
                monthlyPayment = loanAmount / numberOfPayments;
            }
            else
            {
                double factor = Math.Pow(1 + monthlyRate, numberOfPayments);
                monthlyPayment = loanAmount * (monthlyRate * factor) / (factor - 1);
            }

            // Calculate totals
            double totalPayments = monthlyPayment * numberOfPayments;
            double totalInterest = totalPayments - loanAmount;

            return $"Mortgage Payment Calculation Results:\n" +
                   $"• Loan Amount: ${loanAmount:N2}\n" +
                   $"• Interest Rate: {annualInterestRate}% annually\n" +
                   $"• Loan Term: {loanTermYears} years ({numberOfPayments} payments)\n" +
                   $"• Monthly Payment: ${monthlyPayment:N2}\n" +
                   $"• Total of Payments: ${totalPayments:N2}\n" +
                   $"• Total Interest: ${totalInterest:N2}";
        }
        catch (Exception ex)
        {
            return $"Error calculating mortgage payment: {ex.Message}";
        }
    }

    /// <summary>
    /// Determines affordability based on income and debt-to-income ratio
    /// </summary>
    [KernelFunction]
    [Description("Determines loan affordability based on monthly income and desired debt-to-income ratio")]
    public string CalculateAffordability(
        [Description("Monthly gross income in dollars")] double monthlyIncome,
        [Description("Existing monthly debt payments in dollars")] double existingMonthlyDebt,
        [Description("Maximum debt-to-income ratio as a percentage (e.g., 43 for 43%)")] double maxDtiRatio = 43.0)
    {
        try
        {
            if (monthlyIncome <= 0)
            {
                return "Error: Monthly income must be positive.";
            }

            if (maxDtiRatio <= 0 || maxDtiRatio > 100)
            {
                return "Error: DTI ratio must be between 0 and 100.";
            }

            double maxTotalDebt = monthlyIncome * (maxDtiRatio / 100);
            double availableForHousing = maxTotalDebt - existingMonthlyDebt;

            if (availableForHousing <= 0)
            {
                return $"Affordability Analysis Results:\n" +
                       $"• Monthly Income: ${monthlyIncome:N2}\n" +
                       $"• Existing Monthly Debt: ${existingMonthlyDebt:N2}\n" +
                       $"• Maximum DTI Ratio: {maxDtiRatio}%\n" +
                       $"• Maximum Total Monthly Debt: ${maxTotalDebt:N2}\n" +
                       $"• Available for Housing: ${availableForHousing:N2}\n" +
                       $"• Assessment: Current debt level exceeds DTI guidelines. Consider paying down existing debt before applying for a mortgage.";
            }

            return $"Affordability Analysis Results:\n" +
                   $"• Monthly Income: ${monthlyIncome:N2}\n" +
                   $"• Existing Monthly Debt: ${existingMonthlyDebt:N2}\n" +
                   $"• Maximum DTI Ratio: {maxDtiRatio}%\n" +
                   $"• Maximum Total Monthly Debt: ${maxTotalDebt:N2}\n" +
                   $"• Available for Housing Payment: ${availableForHousing:N2}\n" +
                   $"• Assessment: You can afford a housing payment up to ${availableForHousing:N2} per month while staying within DTI guidelines.";
        }
        catch (Exception ex)
        {
            return $"Error calculating affordability: {ex.Message}";
        }
    }

    /// <summary>
    /// Estimates loan amount based on down payment and purchase price
    /// </summary>
    [KernelFunction]
    [Description("Calculates loan amount based on home purchase price and down payment")]
    public string CalculateLoanAmount(
        [Description("Home purchase price in dollars")] double purchasePrice,
        [Description("Down payment amount in dollars")] double downPayment)
    {
        try
        {
            if (purchasePrice <= 0)
            {
                return "Error: Purchase price must be positive.";
            }

            if (downPayment < 0)
            {
                return "Error: Down payment cannot be negative.";
            }

            if (downPayment >= purchasePrice)
            {
                return "Error: Down payment cannot be greater than or equal to the purchase price.";
            }

            double loanAmount = purchasePrice - downPayment;
            double downPaymentPercentage = (downPayment / purchasePrice) * 100;

            return $"Loan Amount Calculation Results:\n" +
                   $"• Purchase Price: ${purchasePrice:N2}\n" +
                   $"• Down Payment: ${downPayment:N2} ({downPaymentPercentage:F1}%)\n" +
                   $"• Loan Amount: ${loanAmount:N2}\n" +
                   $"• Loan-to-Value Ratio: {(loanAmount / purchasePrice) * 100:F1}%";
        }
        catch (Exception ex)
        {
            return $"Error calculating loan amount: {ex.Message}";
        }
    }
}
