using CalmCadence.Core.Models;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace CalmCadence.Data.Configurations;

public class ProjectConfiguration : IEntityTypeConfiguration<Project>
{
    public void Configure(EntityTypeBuilder<Project> builder)
    {
        builder.ToTable("Projects");
        builder.HasKey(p => p.Id);
        builder.Property(p => p.Name).IsRequired().HasMaxLength(200);
        builder.Property(p => p.Description).HasMaxLength(2000);
        builder.Property(p => p.ColorHex).HasMaxLength(9); // e.g., #RRGGBBAA
        builder.Property(p => p.CreatedAt).IsRequired();

        builder.HasMany(p => p.Tasks)
               .WithOne(t => t.Project)
               .HasForeignKey(t => t.ProjectId)
               .OnDelete(DeleteBehavior.SetNull);

        builder.HasIndex(p => p.Name);
    }
}
