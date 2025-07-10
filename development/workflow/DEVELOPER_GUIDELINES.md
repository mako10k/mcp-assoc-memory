# Developer Guidelines and Best Practices

## Knowledge Management Workflow

### LLM Knowledge Update Process
When encountering unknown or potentially outdated information:

1. **Check Existing Knowledge**: First check `docs/knowledges/<knowledge_name>.md`
2. **Research Latest Information**: Use `google_search`, `fetch_webpage`, or `github_repo` tools
3. **Document Findings**: Save results to `docs/knowledges/<knowledge_name>.md` 
4. **Apply Changes**: Modify code based on updated knowledge
5. **Record Lessons Learned**: Document successful solutions and common pitfalls

This process ensures LLM knowledge stays current with real-world best practices.

### Knowledge Categories
- **API Documentation**: Latest SDK and library usage patterns
- **Implementation Patterns**: Proven solutions and architectures  
- **Common Pitfalls**: Frequently encountered issues and solutions
- **Performance Optimizations**: Benchmarked improvements and techniques

## Development Philosophy

### Library-First Approach
- **Avoid Custom Implementation**: Prefer existing SDKs and libraries over custom solutions
- **Leverage Ecosystem**: Maximize use of proven tools and frameworks
- **Standard Patterns**: Follow established patterns rather than inventing new ones
- **Community Solutions**: Research existing solutions before building from scratch

### Research and Documentation
- **Knowledge Validation**: Always verify LLM knowledge against current documentation
- **Tool-Assisted Research**: Use `google_search`, `fetch_webpage`, `github_repo` for latest information
- **Documentation-First**: Document findings before implementing solutions
- **Lesson Recording**: Capture both successes and common pitfalls for future reference

## File Management

### Log File Maintenance
- **Frequency**: Clean up during Git commits or weekly
- **Location**: `.copilot-temp/` directory  
- **Retention**: Keep recent logs for debugging, remove old ones
- **Automation**: Consider automated cleanup scripts

### Temporary Files
- Use `.copilot-temp/` for all temporary outputs
- Include timestamp and sequence numbers in filenames
- Clean up after major development milestones

## Code Quality Standards

### Documentation Requirements
- **API Changes**: Document all public interface modifications
- **Complex Logic**: Explain non-obvious algorithmic decisions
- **External Dependencies**: Document why specific libraries were chosen
- **Performance Implications**: Note computational complexity and memory usage

### Testing Guidelines
- **Unit Tests**: Cover core business logic
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Validate complete user workflows
- **Performance Tests**: Benchmark critical paths

## Architecture Principles

### Modular Design
- **Single Responsibility**: Each module has one clear purpose
- **Loose Coupling**: Minimize dependencies between components
- **High Cohesion**: Related functionality stays together
- **Interface Segregation**: Small, focused interfaces

### Error Handling
- **Graceful Degradation**: System continues operating with reduced functionality
- **Comprehensive Logging**: Capture context for debugging
- **User-Friendly Messages**: Clear error communication to end users
- **Recovery Mechanisms**: Automatic retry and fallback strategies

## Performance Considerations

### Optimization Priorities
1. **Correctness**: Functionality must work as specified
2. **Readability**: Code must be maintainable
3. **Performance**: Optimize bottlenecks after profiling
4. **Resource Usage**: Consider memory and CPU constraints

### Monitoring and Metrics
- **Response Times**: Track API and search performance
- **Memory Usage**: Monitor for memory leaks and excessive consumption
- **Error Rates**: Alert on increased failure rates
- **User Experience**: Measure end-to-end task completion times

## Security Guidelines

### Data Protection
- **Input Validation**: Sanitize all user inputs
- **Access Controls**: Implement proper authentication/authorization
- **Data Encryption**: Protect sensitive data in transit and at rest
- **Audit Logging**: Track access to sensitive operations

### Dependency Management
- **Regular Updates**: Keep dependencies current with security patches
- **Vulnerability Scanning**: Regular security audits of dependencies  
- **Minimal Dependencies**: Only include necessary external libraries
- **License Compliance**: Ensure all dependencies have compatible licenses

## Collaboration Standards

### Code Reviews
- **Required for All Changes**: No direct commits to main branch
- **Focus Areas**: Logic correctness, performance, security, maintainability
- **Documentation Updates**: Ensure docs stay synchronized with code
- **Test Coverage**: Verify adequate testing of new functionality

### Communication
- **Clear Commit Messages**: Describe what and why, not just how
- **Issue Tracking**: Link code changes to relevant issues/requirements
- **Design Discussions**: Document architectural decisions and trade-offs
- **Knowledge Sharing**: Regular team updates on lessons learned

## Maintenance Workflows

### Regular Maintenance Tasks
- **Dependency Updates**: Monthly review and update cycle
- **Performance Monitoring**: Weekly review of metrics and logs
- **Security Audits**: Quarterly security assessment
- **Documentation Reviews**: Ensure accuracy and completeness

### Technical Debt Management
- **Identify**: Regular code quality assessments
- **Prioritize**: Balance new features with technical debt
- **Plan**: Include refactoring in sprint planning
- **Execute**: Allocate dedicated time for improvements

## Emergency Procedures

### Incident Response
1. **Immediate**: Stop or rollback problematic changes
2. **Assess**: Determine scope and impact of the issue
3. **Communicate**: Notify stakeholders of status and timeline
4. **Fix**: Implement solution with appropriate testing
5. **Review**: Post-incident analysis and prevention measures

### Backup and Recovery
- **Regular Backups**: Automated daily backups of critical data
- **Recovery Testing**: Regular validation of backup restoration
- **Documentation**: Clear procedures for emergency recovery
- **Redundancy**: Multiple backup locations and methods
